# Vanishing Docket: Volatile Memory Dump (4:35-4:50 PM)

- **Category:** Forensics (Timed Bonus)
- **Flag:** `case{volatile_cache_grabbed_before_deletion}`
- **Active Window:** 4:35 PM to 4:50 PM (15 Minutes)

## Concept & Solution
Run:
`strings files/volatile_swap_fragment.raw | grep -i "case{"`
to quickly retrieve the volatile flag before the round expires!
