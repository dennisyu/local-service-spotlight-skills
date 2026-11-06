# Google Ads Script, Code Patterns Reference

Copy-paste-ready utility functions for common operations across Google Ads Scripts. Each pattern is production-ready with error handling and JSDoc comments.

---

## Sheet Helpers

### getOrCreateSheet
```javascript
/**
 * Gets an existing sheet by name, or creates it if it doesn't exist.
 * @param {string} spreadsheetUrl - Full URL to the Google Sheet
 * @param {string} sheetName - Name of the sheet to access/create
 * @returns {Sheet} The sheet object
 */
function getOrCreateSheet(spreadsheetUrl, sheetName) {
  const ss = SpreadsheetApp.openByUrl(spreadsheetUrl);
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  return sheet;
}
```

### writeHeaders
```javascript
/**
 * Writes header row and applies bold formatting.
 * @param {Sheet} sheet - The sheet to write to
 * @param {string[]} headers - Array of header names
 */
function writeHeaders(sheet, headers) {
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
}
```

### appendRows
```javascript
/**
 * Appends rows to sheet. Uses batch write for performance (>100 rows).
 * @param {Sheet} sheet - The sheet to append to
 * @param {Array<Array>} dataArray - 2D array of data rows
 */
function appendRows(sheet, dataArray) {
  if (!dataArray || dataArray.length === 0) return;

  const lastRow = sheet.getLastRow();
  const range = sheet.getRange(lastRow + 1, 1, dataArray.length, dataArray[0].length);
  range.setValues(dataArray);
}
```

### clearAndWrite
```javascript
/**
 * Clears sheet and writes fresh headers + data rows.
 * @param {Sheet} sheet - The sheet to clear and populate
 * @param {string[]} headers - Header row
 * @param {Array<Array>} dataArray - 2D array of data rows
 */
function clearAndWrite(sheet, headers, dataArray) {
  sheet.clear();
  writeHeaders(sheet, headers);
  if (dataArray && dataArray.length > 0) {
    appendRows(sheet, dataArray);
  }
}
```

### formatAsTable
```javascript
/**
 * Formats sheet as a table: bold headers, auto-resize columns, light background.
 * @param {Sheet} sheet - The sheet to format
 * @param {number} numRows - Number of data rows (excluding header)
 * @param {number} numCols - Number of columns
 */
function formatAsTable(sheet, numRows, numCols) {
  // Bold header row
  sheet.getRange(1, 1, 1, numCols).setFontWeight('bold');

  // Auto-resize columns
  sheet.autoResizeColumns(1, numCols);

  // Light gray background for header
  sheet.getRange(1, 1, 1, numCols).setBackground('#f0f0f0');

  // Freeze header row
  sheet.setFrozenRows(1);
}
```

---

## Email Helpers

### sendAlert
```javascript
/**
 * Sends a simple text email alert.
 * @param {string} subject - Email subject
 * @param {string} body - Email body (plain text)
 */
function sendAlert(subject, body) {
  const recipientEmail = Session.getEffectiveUser().getEmail();
  GmailApp.sendEmail(recipientEmail, subject, body);
}
```

### sendHtmlReport
```javascript
/**
 * Sends an HTML email with a formatted table.
 * @param {string} subject - Email subject
 * @param {string[]} headers - Table header row
 * @param {Array<Array>} rows - 2D array of table data
 */
function sendHtmlReport(subject, headers, rows) {
  const html = buildHtmlTable(headers, rows);
  const recipientEmail = Session.getEffectiveUser().getEmail();
  GmailApp.sendEmail(recipientEmail, subject, '', {
    htmlBody: html
  });
}
```

### buildHtmlTable
```javascript
/**
 * Builds an HTML table string from headers and rows.
 * @param {string[]} headers - Table header row
 * @param {Array<Array>} rows - 2D array of table data
 * @returns {string} HTML table string
 */
function buildHtmlTable(headers, rows) {
  let html = '<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; font-family: Arial;">';

  // Header row
  html += '<tr style="background-color: #4285f4; color: white;">';
  headers.forEach(header => {
    html += '<th style="text-align: left;">' + header + '</th>';
  });
  html += '</tr>';

  // Data rows
  rows.forEach((row, idx) => {
    const bgColor = idx % 2 === 0 ? '#ffffff' : '#f9f9f9';
    html += '<tr style="background-color: ' + bgColor + ';">';
    row.forEach(cell => {
      html += '<td>' + (cell !== null ? cell : '') + '</td>';
    });
    html += '</tr>';
  });

  html += '</table>';
  return html;
}
```

---

## Date Helpers

### getYesterday
```javascript
/**
 * Returns yesterday's date as a Date object.
 * @param {string} timezone - Timezone string (e.g., 'America/New_York')
 * @returns {Date} Yesterday at midnight (local timezone)
 */
function getYesterday(timezone) {
  const now = new Date();
  const formatter = Utilities.formatDate(now, timezone, 'yyyy-MM-dd');
  const today = new Date(formatter);
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
  return yesterday;
}
```

### formatDateGAQL
```javascript
/**
 * Formats a Date object to YYYYMMDD string for GAQL queries.
 * @param {Date} date - The date to format
 * @returns {string} YYYYMMDD format (e.g., '20260327')
 */
function formatDateGAQL(date) {
  return Utilities.formatDate(date, 'UTC', 'yyyyMMdd');
}
```

### formatDateDisplay
```javascript
/**
 * Formats a Date object to human-readable display format.
 * @param {Date} date - The date to format
 * @param {string} timezone - Timezone string (e.g., 'America/New_York')
 * @returns {string} Display format (e.g., 'Mar 27, 2026')
 */
function formatDateDisplay(date, timezone) {
  return Utilities.formatDate(date, timezone, 'MMM dd, yyyy');
}
```

### getDateRange
```javascript
/**
 * Returns start and end dates for a range (e.g., last 30 days).
 * @param {number} daysBack - Number of days to go back
 * @param {string} timezone - Timezone string
 * @returns {object} {start: 'YYYYMMDD', end: 'YYYYMMDD'}
 */
function getDateRange(daysBack, timezone) {
  const endDate = new Date();
  const startDate = new Date(endDate.getTime() - daysBack * 24 * 60 * 60 * 1000);

  return {
    start: formatDateGAQL(startDate),
    end: formatDateGAQL(endDate)
  };
}
```

### getLastMonday
```javascript
/**
 * Returns the most recent Monday at midnight (for weekly reports).
 * @param {string} timezone - Timezone string
 * @returns {Date} Last Monday
 */
function getLastMonday(timezone) {
  const now = new Date();
  const day = now.getDay();
  const diff = (day === 0 ? 6 : day - 1); // 0 = Sunday, 1 = Monday
  const lastMonday = new Date(now.getTime() - diff * 24 * 60 * 60 * 1000);

  // Reset to midnight in the timezone
  const formatter = Utilities.formatDate(lastMonday, timezone, 'yyyy-MM-dd');
  return new Date(formatter);
}
```

---

## Cost Conversion

### microsToDecimal
```javascript
/**
 * Converts micros (Google Ads format) to decimal currency.
 * @param {number} micros - Amount in micros
 * @returns {number} Decimal amount
 */
function microsToDecimal(micros) {
  return micros / 1000000;
}
```

### formatCurrency
```javascript
/**
 * Formats a number as USD currency string.
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency (e.g., '$12.34')
 */
function formatCurrency(amount) {
  return '$' + parseFloat(amount).toFixed(2);
}
```

---

## BigQuery Helpers

### ensureDatasetExists
```javascript
/**
 * Creates a BigQuery dataset if it doesn't exist.
 * @param {string} projectId - GCP project ID
 * @param {string} datasetId - Dataset ID to create/verify
 */
function ensureDatasetExists(projectId, datasetId) {
  const bq = BigQuery.Datasets.list(projectId);
  const exists = bq.datasets && bq.datasets.some(d => d.datasetReference.datasetId === datasetId);

  if (!exists) {
    const dataset = {
      datasetReference: {
        projectId: projectId,
        datasetId: datasetId
      },
      location: 'US'
    };
    BigQuery.Datasets.insert(dataset, projectId);
  }
}
```

### ensureTableExists
```javascript
/**
 * Creates a BigQuery table if it doesn't exist.
 * @param {string} projectId - GCP project ID
 * @param {string} datasetId - Dataset ID
 * @param {string} tableId - Table ID to create/verify
 * @param {Array<object>} schema - Table schema (array of {name, type, mode})
 */
function ensureTableExists(projectId, datasetId, tableId, schema) {
  try {
    BigQuery.Tables.get(projectId, datasetId, tableId);
  } catch (e) {
    // Table doesn't exist, create it
    const table = {
      tableReference: {
        projectId: projectId,
        datasetId: datasetId,
        tableId: tableId
      },
      schema: {
        fields: schema
      }
    };
    BigQuery.Tables.insert(table, projectId, datasetId);
  }
}
```

### insertRowsBatched
```javascript
/**
 * Inserts rows into BigQuery in batches for efficiency.
 * @param {string} projectId - GCP project ID
 * @param {string} datasetId - Dataset ID
 * @param {string} tableId - Table ID
 * @param {Array<object>} rows - Rows to insert
 * @param {number} batchSize - Number of rows per batch (default 500)
 */
function insertRowsBatched(projectId, datasetId, tableId, rows, batchSize = 500) {
  for (let i = 0; i < rows.length; i += batchSize) {
    const batch = rows.slice(i, i + batchSize);
    const insertRequest = {
      rows: batch.map(row => ({ json: row }))
    };
    BigQuery.Tabledata.insertAll(insertRequest, projectId, datasetId, tableId);
  }
}
```

### runQuery
```javascript
/**
 * Runs a synchronous BigQuery query and returns results.
 * @param {string} projectId - GCP project ID
 * @param {string} sql - SQL query string
 * @returns {Array<object>} Query results
 */
function runQuery(projectId, sql) {
  const request = {
    query: sql,
    useLegacySql: false,
    timeoutMs: 30000
  };
  const queryResults = BigQuery.Jobs.query(request, projectId);
  const rows = [];

  if (queryResults.jobReference) {
    const job = BigQuery.Jobs.getQueryResults(projectId, queryResults.jobReference.jobId);
    if (job.rows) {
      job.rows.forEach(row => {
        const obj = {};
        row.f.forEach((cell, idx) => {
          obj['field' + idx] = cell.v;
        });
        rows.push(obj);
      });
    }
  }
  return rows;
}
```

---

## Error Handling Pattern

### withErrorHandling
```javascript
/**
 * Wraps a function with try/catch logging.
 * @param {Function} fn - Function to execute
 * @param {string} entityName - Name for logging (e.g., 'Campaign 123')
 * @returns {object} {success: boolean, result: any, error: string}
 */
function withErrorHandling(fn, entityName) {
  try {
    const result = fn();
    logInfo('SUCCESS: ' + entityName);
    return { success: true, result: result };
  } catch (e) {
    const msg = 'ERROR in ' + entityName + ': ' + e.toString();
    logError(msg);
    return { success: false, error: msg };
  }
}
```

### collectErrors
```javascript
/**
 * Collects error results and returns a formatted summary.
 * @param {Array<object>} errors - Array of error objects with 'entity' and 'error' keys
 * @returns {string} Formatted error summary
 */
function collectErrors(errors) {
  if (errors.length === 0) return '';

  let summary = 'Errors encountered:\n\n';
  errors.forEach(err => {
    summary += '- ' + err.entity + ': ' + err.error + '\n';
  });
  return summary;
}
```

### sendErrorReport
```javascript
/**
 * Sends an error report email if errors occurred.
 * @param {Array<object>} errors - Array of errors
 * @param {string} scriptName - Name of the script for logging
 */
function sendErrorReport(errors, scriptName) {
  if (errors.length === 0) return;

  const errorSummary = collectErrors(errors);
  sendAlert(
    scriptName + ', Error Report',
    errorSummary
  );
}
```

---

## GAQL Helpers

### queryAll
```javascript
/**
 * Executes a GAQL query and handles pagination for large result sets.
 * @param {string} gaqlQuery - GAQL query string
 * @returns {Array<object>} All results across all pages
 */
function queryAll(gaqlQuery) {
  const results = [];
  const pageSize = 10000;
  let pageToken = null;

  while (true) {
    const query = gaqlQuery + (pageToken ? ' LIMIT ' + pageSize + ' OFFSET ' + (results.length) : ' LIMIT ' + pageSize);
    const page = AdsApp.search(query);

    for (let row of page) {
      results.push(row);
    }

    if (!page.hasNext()) break;
    pageToken = page.getStartIndex() + page.getRowCount();
  }

  return results;
}
```

### queryToArray
```javascript
/**
 * Executes GAQL query and maps results to an array of objects.
 * @param {string} gaqlQuery - GAQL query string
 * @param {Function} fieldMapper - Function that maps row to object {row => ({...})}
 * @returns {Array<object>} Mapped results
 */
function queryToArray(gaqlQuery, fieldMapper) {
  const results = [];
  const page = AdsApp.search(gaqlQuery);

  for (let row of page) {
    results.push(fieldMapper(row));
  }

  return results;
}
```

---

## MCC Patterns

### main (MCC entry point)
```javascript
/**
 * Main entry point for MCC scripts. Executes function across all accounts.
 */
function main() {
  const accountSelector = AdsManagerApp.accounts();
  accountSelector.executeInParallel('processAccount', 'afterAllAccounts');
}
```

### processAccount (MCC worker function)
```javascript
/**
 * Processes a single account in an MCC script.
 * Must return a JSON string for aggregation.
 * @returns {string} JSON result string
 */
function processAccount() {
  const account = AdsApp.currentAccount();
  const campaignCount = AdsApp.campaigns().get().totalNumEntities();

  return JSON.stringify({
    customerId: account.getCustomerId(),
    accountName: account.getName(),
    campaignCount: campaignCount,
    timestamp: new Date()
  });
}
```

### afterAllAccounts (MCC aggregation function)
```javascript
/**
 * Processes results from all accounts (called after parallel execution).
 * @param {Array<string>} results - JSON strings from each account
 */
function afterAllAccounts(results) {
  const allData = [];
  const errors = [];

  results.forEach(result => {
    try {
      const parsed = JSON.parse(result);
      allData.push(parsed);
    } catch (e) {
      errors.push({ entity: 'parsing', error: e.toString() });
    }
  });

  logInfo('Processed ' + allData.length + ' accounts');
  if (errors.length > 0) {
    sendErrorReport(errors, 'MCC Script');
  }
}
```

---

## Label Helpers

### ensureLabelExists
```javascript
/**
 * Ensures a label exists; creates it if not.
 * @param {string} labelName - Name of the label
 * @returns {Label} The label object
 */
function ensureLabelExists(labelName) {
  const labels = AdsApp.labels()
    .withCondition('Name = "' + labelName + '"')
    .get();

  if (labels.hasNext()) {
    return labels.next();
  }

  return AdsApp.createLabel(labelName);
}
```

### getEntitiesByLabel
```javascript
/**
 * Retrieves all campaigns with a specific label.
 * @param {string} labelName - Name of the label
 * @returns {Array<Campaign>} Array of campaigns
 */
function getEntitiesByLabel(labelName) {
  const entities = [];
  const campaigns = AdsApp.campaigns()
    .withCondition('Labels CONTAINS "' + labelName + '"')
    .get();

  while (campaigns.hasNext()) {
    entities.push(campaigns.next());
  }

  return entities;
}
```

### applyLabelToEntities
```javascript
/**
 * Applies a label to multiple campaigns or ad groups.
 * @param {Array<Campaign|AdGroup>} entities - Array of campaigns or ad groups
 * @param {string} labelName - Name of the label to apply
 */
function applyLabelToEntities(entities, labelName) {
  const label = ensureLabelExists(labelName);

  entities.forEach(entity => {
    entity.applyLabel(labelName);
  });

  logInfo('Applied label "' + labelName + '" to ' + entities.length + ' entities');
}
```

---

## Logging Pattern

### logInfo
```javascript
/**
 * Logs an info-level message with timestamp.
 * @param {string} msg - Message to log
 */
function logInfo(msg) {
  const timestamp = Utilities.formatDate(new Date(), 'UTC', 'yyyy-MM-dd HH:mm:ss');
  Logger.log('[INFO] ' + timestamp + ', ' + msg);
}
```

### logWarning
```javascript
/**
 * Logs a warning-level message with timestamp.
 * @param {string} msg - Message to log
 */
function logWarning(msg) {
  const timestamp = Utilities.formatDate(new Date(), 'UTC', 'yyyy-MM-dd HH:mm:ss');
  Logger.log('[WARN] ' + timestamp + ', ' + msg);
}
```

### logError
```javascript
/**
 * Logs an error-level message with timestamp.
 * @param {string} msg - Message to log
 */
function logError(msg) {
  const timestamp = Utilities.formatDate(new Date(), 'UTC', 'yyyy-MM-dd HH:mm:ss');
  Logger.log('[ERROR] ' + timestamp + ', ' + msg);
}
```

---

## Usage Notes

- **Sheet helpers**: Always pair `getOrCreateSheet()` with `writeHeaders()` for consistent formatting.
- **Batch operations**: Use batch writes (`appendRows`) instead of row-by-row for >100 rows, 10x faster.
- **Date handling**: Always pass timezone explicitly (e.g., `'America/New_York'`) for consistency across reports.
- **GAQL**: Use `queryAll()` for large datasets; it handles pagination automatically.
- **MCC**: Return JSON strings from worker functions; aggregate in `afterAllAccounts()`.
- **Error handling**: Wrap risky operations in `withErrorHandling()` and collect errors for summary reporting.
- **BigQuery**: Always call `ensureDatasetExists()` and `ensureTableExists()` before inserting rows.
