# Implementation Plan

- [ ] 1. Create RecurringTransaction model
  - Add RecurringTransaction model to finance_models.py with all fields
  - Add relationship to User, Account, and Category models
  - Add is_active and is_paused boolean fields
  - Add next_occurrence date field
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

- [ ] 2. Implement recurrence calculation service
  - Create recurrence_service.py with RecurrenceService class
  - Implement calculate_next_occurrence for daily pattern
  - Implement calculate_next_occurrence for weekly pattern
  - Implement calculate_next_occurrence for monthly pattern (handle month-end edge cases)
  - Implement calculate_next_occurrence for yearly pattern
  - Implement should_generate method to check if transaction is due
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.4, 3.5_

- [ ]* 2.1 Write property test for next occurrence calculation
  - **Property 2: Next occurrence calculation**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 3.4**

- [ ]* 2.2 Write property test for date validation
  - **Property 1: Date validation**
  - **Validates: Requirements 1.5**

- [ ] 3. Implement transaction generation logic
  - Implement generate_transaction method in RecurrenceService
  - Copy all fields from recurring template to new transaction
  - Update account balance based on transaction type
  - Mark generated transaction with source recurring_transaction_id
  - Update next_occurrence date after generation
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ]* 3.1 Write property test for transaction generation
  - **Property 3: Transaction generation**
  - **Validates: Requirements 3.1, 6.4**

- [ ]* 3.2 Write property test for generated transaction properties
  - **Property 4: Generated transaction properties**
  - **Validates: Requirements 3.2**

- [ ]* 3.3 Write property test for balance update
  - **Property 5: Balance update**
  - **Validates: Requirements 3.3**

- [ ] 4. Implement batch generation service
  - Create batch_generation_service.py with BatchGenerationService class
  - Implement process_due_recurring_transactions method
  - Query all active, non-paused recurring transactions where next_occurrence <= today
  - Generate transactions for each due recurring template
  - Return count of generated transactions
  - _Requirements: 10.1, 10.2, 10.3_

- [ ]* 4.1 Write property test for end date enforcement
  - **Property 6: End date enforcement**
  - **Validates: Requirements 3.5**

- [ ] 5. Create recurring transaction routes
  - Create recurring_routes.py Blueprint
  - Implement GET /recurring route to list all recurring transactions
  - Implement GET/POST /recurring/add route for creation with validation
  - Implement GET /recurring/<id> route for detail view
  - Implement GET/POST /recurring/<id>/edit route for updates
  - Implement POST /recurring/<id>/delete route
  - Implement POST /recurring/<id>/pause route
  - Implement POST /recurring/<id>/resume route
  - Implement POST /recurring/<id>/generate route for manual trigger
  - Implement POST /recurring/batch route for manual batch process
  - Register Blueprint in application factory
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 5.1, 5.2, 6.1, 6.2, 7.1, 9.1, 9.2, 10.5_

- [ ]* 5.1 Write property test for pause behavior
  - **Property 7: Pause behavior**
  - **Validates: Requirements 6.1, 6.4**

- [ ]* 5.2 Write property test for historical preservation
  - **Property 8: Historical preservation**
  - **Validates: Requirements 7.2, 5.3**

- [ ] 6. Add recurring_transaction_id to Transaction model
  - Add optional recurring_transaction_id foreign key to Transaction model
  - Add relationship to RecurringTransaction
  - Add is_auto_generated boolean field
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 7. Create recurring transaction templates
  - Create recurring_transactions.html to list all recurring transactions
  - Create add_recurring.html with form including recurrence pattern selection
  - Create edit_recurring.html for editing recurring transactions
  - Create recurring_detail.html showing schedule and generated transactions
  - Add pause/resume buttons to recurring transaction list
  - Display next occurrence date and recurrence pattern
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 6.3_

- [ ] 8. Update transaction display to show auto-generated indicator
  - Add visual indicator for auto-generated transactions in transaction list
  - Display source recurring transaction link on transaction detail page
  - Add filter option for auto-generated vs manual transactions
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 9. Implement automatic batch process on startup
  - Add batch process call to application initialization
  - Log number of transactions generated
  - Handle errors gracefully without blocking startup
  - _Requirements: 10.4_

- [ ] 10. Add navigation and styling
  - Add "Recurring Transactions" link to navigation menu
  - Style recurring transaction cards with recurrence pattern badges
  - Add pause/active status indicators
  - Style manual generation and batch process buttons
  - _Requirements: All_

- [ ] 11. Create database migration
  - Generate migration for RecurringTransaction table
  - Add recurring_transaction_id and is_auto_generated to Transaction table
  - Test migration up and down
  - _Requirements: All_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
