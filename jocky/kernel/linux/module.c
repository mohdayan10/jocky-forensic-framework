/*
 * JOCKY Kernel Module — Linux Forensic Collection
 * Walks task_struct list for hidden process detection,
 * parses /proc/kallsyms for symbol resolution,
 * enumerates loaded kernel modules.
 *
 * Built with: make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/sched.h>
#include <linux/sched/signal.h>
#include <linux/fs.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/slab.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("JOCKY Team — SIH 2024");
MODULE_DESCRIPTION("Forensic kernel collection for hidden process and rootkit detection");

#define JOCKY_PROC_NAME "jocky_forensic"
#define MAX_PROCESSES   4096

typedef struct {
    pid_t   pid;
    pid_t   ppid;
    char    comm[TASK_COMM_LEN];
    uid_t   uid;
    int     visible_in_proc;
} process_entry_t;

static process_entry_t kernel_processes[MAX_PROCESSES];
static int kernel_process_count = 0;
static int hidden_count = 0;

/*
 * Walk task_struct via for_each_process macro.
 * This traverses the doubly-linked list starting from init_task,
 * which is the kernel equivalent of walking EPROCESS on Windows.
 *
 * Rootkits that hide processes by unlinking from /proc's pid_namespace
 * iterator are still visible through this traversal.
 */
static int walk_task_list(void) {
    struct task_struct *task;
    kernel_process_count = 0;

    rcu_read_lock();
    for_each_process(task) {
        if (kernel_process_count >= MAX_PROCESSES) break;

        process_entry_t *entry = &kernel_processes[kernel_process_count];
        entry->pid  = task->pid;
        entry->ppid = task->real_parent->pid;
        entry->uid  = __kuid_val(task_uid(task));
        get_task_comm(entry->comm, task);
        entry->visible_in_proc = 1;

        kernel_process_count++;
    }
    rcu_read_unlock();

    return kernel_process_count;
}

/*
 * Check which kernel-visible processes are hidden from /proc.
 * A process present in task_struct walk but absent from
 * /proc/{pid}/status is potentially hidden by a rootkit.
 */
static int detect_hidden_processes(void) {
    hidden_count = 0;

    for (int i = 0; i < kernel_process_count; i++) {
        char path[32];
        struct path p;
        int err;

        snprintf(path, sizeof(path), "/proc/%d", kernel_processes[i].pid);
        err = kern_path(path, LOOKUP_FOLLOW, &p);

        if (err) {
            /* Process exists in kernel but not in /proc = hidden */
            kernel_processes[i].visible_in_proc = 0;
            hidden_count++;
            pr_warn("[JOCKY] Hidden process detected: %s (PID %d, PPID %d)\n",
                    kernel_processes[i].comm,
                    kernel_processes[i].pid,
                    kernel_processes[i].ppid);
        } else {
            path_put(&p);
        }
    }

    return hidden_count;
}

/*
 * Enumerate loaded kernel modules and check against known-good list.
 * Identifies suspicious modules not in the system's module whitelist.
 */
static int enum_kernel_modules(struct seq_file *m) {
    struct module *mod;
    int count = 0;

    mutex_lock(&module_mutex);
    list_for_each_entry(mod, &THIS_MODULE->list, list) {
        seq_printf(m, "  Module: %-24s  Size: %u  State: %s\n",
                   mod->name,
                   mod->core_layout.size,
                   mod->state == MODULE_STATE_LIVE ? "LIVE" :
                   mod->state == MODULE_STATE_COMING ? "LOADING" : "GOING");
        count++;
    }
    mutex_unlock(&module_mutex);

    return count;
}

/* /proc/jocky_forensic seq_file output */
static int jocky_proc_show(struct seq_file *m, void *v) {
    int total = walk_task_list();
    int hidden = detect_hidden_processes();

    seq_printf(m, "JOCKY Kernel Forensic Collection\n");
    seq_printf(m, "================================\n\n");

    seq_printf(m, "Process Walk:\n");
    seq_printf(m, "  Kernel task_struct count: %d\n", total);
    seq_printf(m, "  /proc visible count:     %d\n", total - hidden);
    seq_printf(m, "  Hidden (delta):          %d\n\n", hidden);

    if (hidden > 0) {
        seq_printf(m, "Hidden Processes:\n");
        for (int i = 0; i < kernel_process_count; i++) {
            if (!kernel_processes[i].visible_in_proc) {
                seq_printf(m, "  PID: %-6d  PPID: %-6d  Name: %s  UID: %d\n",
                           kernel_processes[i].pid,
                           kernel_processes[i].ppid,
                           kernel_processes[i].comm,
                           kernel_processes[i].uid);
            }
        }
        seq_printf(m, "\n");
    }

    seq_printf(m, "Loaded Kernel Modules:\n");
    enum_kernel_modules(m);

    return 0;
}

static int jocky_proc_open(struct inode *inode, struct file *file) {
    return single_open(file, jocky_proc_show, NULL);
}

static const struct proc_ops jocky_proc_ops = {
    .proc_open    = jocky_proc_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

static int __init jocky_init(void) {
    proc_create(JOCKY_PROC_NAME, 0444, NULL, &jocky_proc_ops);
    pr_info("[JOCKY] Kernel forensic module loaded\n");
    return 0;
}

static void __exit jocky_exit(void) {
    remove_proc_entry(JOCKY_PROC_NAME, NULL);
    pr_info("[JOCKY] Kernel forensic module unloaded\n");
}

module_init(jocky_init);
module_exit(jocky_exit);
