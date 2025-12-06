# Implementation Plan

- [ ] 1. Create Goal and GoalContribution models
  - Add Goal model to finance_models.py with all fields and relationships
  - Add GoalContribution model to finance_models.py
  - Add GoalAccountLink association table
  - Add goals relationship to User model
  - Add linked_goals relationship to Account model
  - Implement property methods (progress_percentage, is_achieved, is_overdue, days_remaining)
  - _Requirements: 1.1, 1.2, 1.3, 1.6, 2.4, 3.2, 3.3, 3.4, 3.5, 8.1_

- [ ]* 1.1 Write property test for initial amount invariant
  - **Property 2: Initial amount invariant**
  - **Validates: Requirements 1.6**

- [ ]* 1.2 Write property test for progress calculation
  - **Property 4: Progress calculation correctness**
  - **Validates: Requirements 3.2, 2.5**

- [ ]* 1.3 Write property test for achievement status
  - **Property 5: Achievement status**
  - **Validates: Requirements 3.5**

- [ ]* 1.4 Write property test for overdue status
  - **Property 6: Overdue status**
  - **Validates: Requirements 3.4**

- [ ] 2. Implement goal validation and service layer
  - Create goal_service.py with GoalService class
  - Implement validate_goal_data method for target amount and deadline validation
  - Implement calculation helper methods
  - _Requirements: 1.4, 1.5, 3.2, 3.3, 3.4, 3.5_

- [ ]* 2.1 Write property test for goal validation
  - **Property 1: Goal validation**
  - **Validates: Requirements 1.4, 1.5**

- [ ] 3. Implement goal repository
  - Create goal_repository.py with GoalRepository class
  - Implement get_user_goals method with optional achieved filter
  - Implement get_goal_by_id method with user authorization check
  - Implement get_goal_statistics method for dashboard aggregations
  - _Requirements: 3.1, 9.1, 9.2, 9.3, 9.4_

- [ ]* 3.1 Write property test for dashboard statistics
  - **Property 12: Dashboard statistics accuracy**
  - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

- [ ] 4. Create goal routes and CRUD operations
  - Create goal_routes.py Blueprint
  - Implement GET /goals route to list all user goals
  - Implement GET/POST /goals/add route for goal creation with validation
  - Implement GET /goals/<id> route for goal detail view
  - Implement GET/POST /goals/<id>/edit route for goal updates
  - Implement POST /goals/<id>/delete route with cascade deletion
  - Register Blueprint in application factory
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.4, 5.1, 5.3_

- [ ]* 4.1 Write property test for current amount immutability
  - **Property 11: Current amount immutability**
  - **Validates: Requirements 4.2**

- [ ]* 4.2 Write property test for cascade deletion
  - **Property 9: Cascade deletion**
  - **Validates: Requirements 5.1**

- [ ]* 4.3 Write property test for data isolation
  - **Property 10: Data isolation**
  - **Validates: Requirements 5.3**

- [ ] 5. Implement contribution functionality
  - Implement POST /goals/<id>/contribute route for adding contributions
  - Validate contribution amount is positive
  - Update goal current_amount when contribution is added
  - Recalculate progress percentage after contribution
  - Store contribution with date and optional note
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 5.1 Write property test for contribution accumulation
  - **Property 3: Contribution accumulation**
  - **Validates: Requirements 2.1**

- [ ] 6. Create goal templates
  - Create goals.html template to list all goals with progress bars
  - Create add_goal.html template with form for goal creation
  - Create goal_detail.html template showing goal info and contribution history
  - Create edit_goal.html template for goal editing
  - Add contribution form to goal detail page
  - Display progress bars with color coding based on percentage
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 6.1, 6.2, 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 6.1 Write property test for contribution ordering
  - **Property 8: Contribution ordering**
  - **Validates: Requirements 6.1**

- [ ] 7. Implement account linking functionality
  - Add account selection to goal creation and edit forms
  - Store goal-account links in GoalAccountLink table
  - Display linked accounts on goal detail page
  - Handle account deletion (remove link, preserve goal)
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 8. Add goal statistics to dashboard
  - Update dashboard_routes.py to fetch goal statistics
  - Display total active goals count
  - Display achieved goals count
  - Display total target amount across all goals
  - Display total current amount across all goals
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 9. Add navigation and styling
  - Add "Goals" link to navigation menu
  - Style goal cards and progress bars
  - Add responsive design for mobile viewing
  - Style contribution history table
  - Add visual indicators for overdue and achieved goals
  - _Requirements: All_

- [ ] 10. Create database migration
  - Generate migration script for Goal, GoalContribution, and GoalAccountLink tables
  - Test migration up and down
  - _Requirements: All_

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
