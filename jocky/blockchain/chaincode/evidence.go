// SPDX-License-Identifier: Apache-2.0
// Hyperledger Fabric chaincode for JOCKY evidence integrity ledger.
// Deploys to peer0.ntro.gov.in, peer0.agency.gov.in, peer0.auditor.org.

package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type EvidenceContract struct {
	contractapi.Contract
}

type EvidenceRecord struct {
	EvidenceID   string `json:"evidence_id"`
	CaseID       string `json:"case_id"`
	SHA256       string `json:"sha256"`
	AnchoredAt   string `json:"anchored_at"`
	AnchorNode   string `json:"anchor_node"`
	ArtifactType string `json:"artifact_type"`
	Immutable    bool   `json:"immutable"`
}

type VerifyResult struct {
	EvidenceID  string `json:"evidence_id"`
	OnChain     string `json:"on_chain_hash"`
	Current     string `json:"current_hash"`
	Match       bool   `json:"match"`
	VerifiedAt  string `json:"verified_at"`
}

func (ec *EvidenceContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	return nil
}

// AnchorEvidence stores an evidence hash on-chain. Write-once: rejects if
// the evidence ID already exists, enforcing immutability.
func (ec *EvidenceContract) AnchorEvidence(
	ctx contractapi.TransactionContextInterface,
	evidenceID string,
	caseID string,
	hash string,
	artifactType string,
) error {
	existing, err := ctx.GetStub().GetState(evidenceID)
	if err != nil {
		return fmt.Errorf("failed to read state: %v", err)
	}
	if existing != nil {
		return fmt.Errorf("evidence %s already anchored — immutable record", evidenceID)
	}

	mspID, err := ctx.GetClientIdentity().GetMSPID()
	if err != nil {
		return fmt.Errorf("failed to get MSP ID: %v", err)
	}

	record := EvidenceRecord{
		EvidenceID:   evidenceID,
		CaseID:       caseID,
		SHA256:       hash,
		AnchoredAt:   time.Now().UTC().Format(time.RFC3339),
		AnchorNode:   mspID,
		ArtifactType: artifactType,
		Immutable:    true,
	}

	recordJSON, err := json.Marshal(record)
	if err != nil {
		return fmt.Errorf("failed to marshal record: %v", err)
	}

	return ctx.GetStub().PutState(evidenceID, recordJSON)
}

// QueryEvidence retrieves the on-chain record for an evidence ID.
func (ec *EvidenceContract) QueryEvidence(
	ctx contractapi.TransactionContextInterface,
	evidenceID string,
) (*EvidenceRecord, error) {
	recordJSON, err := ctx.GetStub().GetState(evidenceID)
	if err != nil {
		return nil, fmt.Errorf("failed to read state: %v", err)
	}
	if recordJSON == nil {
		return nil, fmt.Errorf("evidence %s not found on ledger", evidenceID)
	}

	var record EvidenceRecord
	if err := json.Unmarshal(recordJSON, &record); err != nil {
		return nil, fmt.Errorf("failed to unmarshal record: %v", err)
	}
	return &record, nil
}

// VerifyEvidence recomputes the hash from provided payload bytes and
// compares against the on-chain record.
func (ec *EvidenceContract) VerifyEvidence(
	ctx contractapi.TransactionContextInterface,
	evidenceID string,
	payloadHex string,
) (*VerifyResult, error) {
	record, err := ec.QueryEvidence(ctx, evidenceID)
	if err != nil {
		return nil, err
	}

	payload, err := hex.DecodeString(payloadHex)
	if err != nil {
		return nil, fmt.Errorf("invalid payload hex: %v", err)
	}

	h := sha256.Sum256(payload)
	currentHash := hex.EncodeToString(h[:])

	result := &VerifyResult{
		EvidenceID: evidenceID,
		OnChain:    record.SHA256,
		Current:    currentHash,
		Match:      currentHash == record.SHA256,
		VerifiedAt: time.Now().UTC().Format(time.RFC3339),
	}
	return result, nil
}

// GetAuditTrail returns all evidence records for a case using a range query.
func (ec *EvidenceContract) GetAuditTrail(
	ctx contractapi.TransactionContextInterface,
	caseID string,
) ([]*EvidenceRecord, error) {
	iterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, fmt.Errorf("failed to get state iterator: %v", err)
	}
	defer iterator.Close()

	var records []*EvidenceRecord
	for iterator.HasNext() {
		result, err := iterator.Next()
		if err != nil {
			return nil, err
		}

		var record EvidenceRecord
		if err := json.Unmarshal(result.Value, &record); err != nil {
			continue
		}
		if record.CaseID == caseID {
			records = append(records, &record)
		}
	}
	return records, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&EvidenceContract{})
	if err != nil {
		fmt.Printf("Error creating evidence chaincode: %v\n", err)
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting evidence chaincode: %v\n", err)
	}
}
