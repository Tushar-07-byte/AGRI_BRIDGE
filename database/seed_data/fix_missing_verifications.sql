-- =========================================
-- FIX MISSING PENDING VERIFICATION RECORDS
-- =========================================
-- This script creates pending verification
-- records for existing listings that do not
-- yet have a verification record.
--
-- Existing verified records are preserved:
--   listing 1  -> verified (Agent Rahul)
--   listing 2  -> verified (Agent Rahul)
--   listing 6  -> verified (Agent Rahul)
--   listing 7  -> verified (Agent Rahul)
--   listing 8  -> verified (Agent Rahul)
-- =========================================

USE agribridge_test;

-- Create pending verification for every
-- listing that does NOT already have a
-- verification record.

INSERT INTO verifications
    (listing_id, agent_name, status, remarks, created_at)
SELECT
    l.id,
    NULL,
    'pending',
    'Awaiting field-agent verification.',
    NOW()
FROM listings l
WHERE NOT EXISTS (
    SELECT 1
    FROM verifications v
    WHERE v.listing_id = l.id
);

-- Verify results

SELECT
    v.id        AS verification_id,
    v.listing_id,
    v.status,
    v.remarks,
    v.created_at
FROM verifications v
ORDER BY v.id;
