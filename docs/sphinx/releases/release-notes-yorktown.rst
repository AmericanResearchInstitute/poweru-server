.. _release-notes-yorktown:

========================
Release Notes - Yorktown
========================

Backwards-Incompatible Changes
==============================

 * [5703] 'msrp' attributes renamed to 'cost'
 * [5703] SessionUserRoleRequirementManager's create method signature
   changed to include a new parameter, 'require_enrollment_fee'
 * [5703] SessionFees and EventFees are gone, EnrollmentFees are added
 * [5703] SessionUserRoleRequirements now have an enrollment_fees
   attribute rather than a session_fees attribute
 * [5703] PurchaseOrderManager - 'total' derived attribute renamed to 'total_price'
 * [5722] Company model renamed to Organization
 * [5723] EventManager's create method signature changed to require an organization before a product line
