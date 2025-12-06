# Implementation Plan

- [x] 1. Create data transfer objects and service layer


  - Create DTOs (ReportData, CategoryBreakdown, AccountSummary, MonthlyData) in a new models/report_models.py file
  - Implement ReportRepository class with query methods for transactions and aggregations
  - Implement ReportService class with report generation and calculation logic
  - _Requirements: 1.1, 1.5, 2.1, 2.2, 2.5, 3.1, 3.2, 7.1_

- [ ]* 1.1 Write property test for financial calculations
  - **Property 2: Financial calculations correctness**
  - **Validates: Requirements 1.5**

- [ ]* 1.2 Write property test for category breakdown
  - **Property 3: Category breakdown completeness**
  - **Validates: Requirements 2.1, 2.2, 2.5**

- [ ]* 1.3 Write property test for total balance calculation
  - **Property 7: Total balance calculation**
  - **Validates: Requirements 3.2**



- [ ] 2. Implement CSV export functionality
  - Create CSVExportService class with transaction export and filename generation methods
  - Implement proper CSV escaping for special characters (commas, quotes, newlines)
  - Add CSV column headers and data formatting
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 2.1 Write property test for CSV structure
  - **Property 8: CSV structure correctness**
  - **Validates: Requirements 4.1, 4.2, 4.4**

- [ ]* 2.2 Write property test for CSV field escaping
  - **Property 9: CSV field escaping**
  - **Validates: Requirements 4.3**

- [ ]* 2.3 Write property test for CSV filename format
  - **Property 10: CSV filename format**

  - **Validates: Requirements 4.5**

- [ ] 3. Implement filtering and validation logic
  - Add date range validation in ReportService (reject if start_date > end_date)
  - Implement transaction type filtering (Income, Expense, All)
  - Implement account filtering logic
  - Add empty category exclusion logic
  - Implement category sorting by amount descending
  - _Requirements: 1.3, 2.3, 2.4, 5.1, 5.2, 5.3, 6.1, 6.2_

- [ ]* 3.1 Write property test for date range validation
  - **Property 1: Date range validation**
  - **Validates: Requirements 1.3**

- [ ]* 3.2 Write property test for transaction type filter
  - **Property 11: Transaction type filter correctness**
  - **Validates: Requirements 5.1, 5.2, 5.3**

- [ ]* 3.3 Write property test for account filter
  - **Property 12: Account filter correctness**
  - **Validates: Requirements 6.1, 6.2**

- [ ]* 3.4 Write property test for category sorting
  - **Property 4: Category sorting**
  - **Validates: Requirements 2.4**

- [x]* 3.5 Write property test for empty category exclusion

  - **Property 5: Empty category exclusion**
  - **Validates: Requirements 2.3**

- [ ] 4. Implement monthly comparison functionality
  - Add monthly aggregation logic in ReportRepository
  - Implement month-over-month percentage change calculation
  - Ensure monthly data is sorted chronologically
  - Calculate net savings for each month
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ]* 4.1 Write property test for monthly aggregation
  - **Property 13: Monthly aggregation correctness**
  - **Validates: Requirements 7.1, 7.3**

- [ ]* 4.2 Write property test for month-over-month calculation
  - **Property 14: Month-over-month calculation**
  - **Validates: Requirements 7.2**



- [ ]* 4.3 Write property test for monthly chronological order
  - **Property 15: Monthly chronological order**
  - **Validates: Requirements 7.4**

- [ ] 5. Create Flask routes and templates
  - Create report_routes.py Blueprint with /reports and /reports/export endpoints
  - Implement GET handler for report form display with date pickers and filter options
  - Implement POST handler for report generation with form data processing
  - Implement POST handler for CSV export with file download response
  - Register Blueprint in application factory
  - _Requirements: 1.1, 1.2, 4.1, 4.5_



- [ ]* 5.1 Write unit tests for route handlers
  - Test report form rendering
  - Test report generation with various filters
  - Test CSV export download
  - Test error handling for invalid inputs

- [ ] 6. Create report display template
  - Create reports.html template with date range and filter form
  - Display summary metrics (total income, expenses, net savings)
  - Display category breakdown tables for income and expenses with percentages

  - Display account summary table with balances
  - Add conditional rendering for empty data states
  - _Requirements: 1.4, 2.1, 2.2, 2.5, 3.1, 3.3_

- [ ]* 6.1 Write property test for account balance display
  - **Property 6: Account balance display**

  - **Validates: Requirements 3.1, 3.3, 3.4**

- [ ] 7. Implement chart data preparation
  - Add methods to prepare data for pie chart (expense by category)
  - Add methods to prepare data for bar chart (income vs expenses)
  - Add methods to prepare data for line chart (monthly trends)
  - Return chart data as JSON for JavaScript consumption


  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 8. Integrate charts into template
  - Add Chart.js library to base template or reports template
  - Create JavaScript functions to render pie chart for expense distribution
  - Create JavaScript functions to render bar chart for income vs expenses comparison
  - Create JavaScript functions to render line chart for monthly trends
  - Handle empty data states with appropriate messaging
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 9. Add navigation and styling
  - Add "Reports" link to navigation menu in base.html
  - Style report forms and tables using existing CSS patterns
  - Add responsive design for mobile viewing
  - Style CSV export button
  - _Requirements: All_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
