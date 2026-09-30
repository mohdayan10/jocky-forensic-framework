/*
 * JOCKY Kernel Driver — DriverEntry + IRP Dispatch
 * Signed kernel driver for forensic collection.
 * Provides IOCTL interface for userspace collector.
 *
 * Built with WDK: msbuild /p:Configuration=Release
 */

#include <ntddk.h>

#define DEVICE_NAME     L"\\Device\\JockyKernel"
#define SYMLINK_NAME    L"\\DosDevices\\JockyKernel"

#define IOCTL_WALK_EPROCESS     CTL_CODE(FILE_DEVICE_UNKNOWN, 0x800, METHOD_BUFFERED, FILE_ANY_ACCESS)
#define IOCTL_ENUM_SSDT         CTL_CODE(FILE_DEVICE_UNKNOWN, 0x801, METHOD_BUFFERED, FILE_ANY_ACCESS)
#define IOCTL_ENUM_CALLBACKS    CTL_CODE(FILE_DEVICE_UNKNOWN, 0x802, METHOD_BUFFERED, FILE_ANY_ACCESS)
#define IOCTL_ENUM_DRIVERS      CTL_CODE(FILE_DEVICE_UNKNOWN, 0x803, METHOD_BUFFERED, FILE_ANY_ACCESS)

DRIVER_DISPATCH JockyDispatchCreate;
DRIVER_DISPATCH JockyDispatchClose;
DRIVER_DISPATCH JockyDispatchDeviceControl;
DRIVER_UNLOAD   JockyUnload;

/* Forward declarations for kernel collection modules */
extern NTSTATUS WalkEprocessList(PVOID OutputBuffer, ULONG OutputLength, PULONG BytesWritten);
extern NTSTATUS EnumSsdtHooks(PVOID OutputBuffer, ULONG OutputLength, PULONG BytesWritten);
extern NTSTATUS EnumCallbacks(PVOID OutputBuffer, ULONG OutputLength, PULONG BytesWritten);
extern NTSTATUS EnumDrivers(PVOID OutputBuffer, ULONG OutputLength, PULONG BytesWritten);

NTSTATUS JockyDispatchCreate(PDEVICE_OBJECT DeviceObject, PIRP Irp) {
    UNREFERENCED_PARAMETER(DeviceObject);
    Irp->IoStatus.Status = STATUS_SUCCESS;
    Irp->IoStatus.Information = 0;
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return STATUS_SUCCESS;
}

NTSTATUS JockyDispatchClose(PDEVICE_OBJECT DeviceObject, PIRP Irp) {
    UNREFERENCED_PARAMETER(DeviceObject);
    Irp->IoStatus.Status = STATUS_SUCCESS;
    Irp->IoStatus.Information = 0;
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return STATUS_SUCCESS;
}

NTSTATUS JockyDispatchDeviceControl(PDEVICE_OBJECT DeviceObject, PIRP Irp) {
    UNREFERENCED_PARAMETER(DeviceObject);

    PIO_STACK_LOCATION irpSp = IoGetCurrentIrpStackLocation(Irp);
    ULONG ioctl = irpSp->Parameters.DeviceIoControl.IoControlCode;
    PVOID outBuffer = Irp->AssociatedIrp.SystemBuffer;
    ULONG outLength = irpSp->Parameters.DeviceIoControl.OutputBufferLength;
    ULONG bytesWritten = 0;
    NTSTATUS status = STATUS_INVALID_DEVICE_REQUEST;

    switch (ioctl) {
    case IOCTL_WALK_EPROCESS:
        status = WalkEprocessList(outBuffer, outLength, &bytesWritten);
        break;
    case IOCTL_ENUM_SSDT:
        status = EnumSsdtHooks(outBuffer, outLength, &bytesWritten);
        break;
    case IOCTL_ENUM_CALLBACKS:
        status = EnumCallbacks(outBuffer, outLength, &bytesWritten);
        break;
    case IOCTL_ENUM_DRIVERS:
        status = EnumDrivers(outBuffer, outLength, &bytesWritten);
        break;
    }

    Irp->IoStatus.Status = status;
    Irp->IoStatus.Information = bytesWritten;
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return status;
}

VOID JockyUnload(PDRIVER_OBJECT DriverObject) {
    UNICODE_STRING symLink;
    RtlInitUnicodeString(&symLink, SYMLINK_NAME);
    IoDeleteSymbolicLink(&symLink);
    IoDeleteDevice(DriverObject->DeviceObject);
    DbgPrint("[JOCKY] Driver unloaded\n");
}

NTSTATUS DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath) {
    UNREFERENCED_PARAMETER(RegistryPath);

    UNICODE_STRING devName, symLink;
    RtlInitUnicodeString(&devName, DEVICE_NAME);
    RtlInitUnicodeString(&symLink, SYMLINK_NAME);

    PDEVICE_OBJECT deviceObject;
    NTSTATUS status = IoCreateDevice(
        DriverObject, 0, &devName,
        FILE_DEVICE_UNKNOWN, FILE_DEVICE_SECURE_OPEN,
        FALSE, &deviceObject);
    if (!NT_SUCCESS(status)) return status;

    status = IoCreateSymbolicLink(&symLink, &devName);
    if (!NT_SUCCESS(status)) {
        IoDeleteDevice(deviceObject);
        return status;
    }

    DriverObject->MajorFunction[IRP_MJ_CREATE]         = JockyDispatchCreate;
    DriverObject->MajorFunction[IRP_MJ_CLOSE]          = JockyDispatchClose;
    DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL] = JockyDispatchDeviceControl;
    DriverObject->DriverUnload = JockyUnload;

    DbgPrint("[JOCKY] Kernel driver loaded — forensic collection ready\n");
    return STATUS_SUCCESS;
}
