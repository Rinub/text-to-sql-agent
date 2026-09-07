/**
 * Self-Healing Text-to-SQL Agent — Frontend App Script
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const form = document.getElementById("query-form");
  const questionInput = document.getElementById("question-input");
  const submitBtn = document.getElementById("submit-btn");
  const btnText = submitBtn.querySelector(".btn-text");
  const spinner = submitBtn.querySelector(".spinner");
  
  const loadingState = document.getElementById("loading-state");
  const resultsSection = document.getElementById("results-section");
  const statusBadge = document.getElementById("status-badge");
  const attemptsBadge = document.getElementById("attempts-badge");
  const rowsBadge = document.getElementById("rows-badge");
  
  const errorAlert = document.getElementById("error-alert");
  const errorMessage = document.getElementById("error-message");
  
  const sqlCode = document.getElementById("sql-code");
  const copySqlBtn = document.getElementById("copy-sql-btn");
  const copyBtnText = document.getElementById("copy-btn-text");
  
  const dataTable = document.getElementById("data-table");
  const jsonCode = document.getElementById("json-code");
  
  const viewTableBtn = document.getElementById("view-table-btn");
  const viewJsonBtn = document.getElementById("view-json-btn");
  const tableContainer = document.getElementById("table-container");
  const jsonContainer = document.getElementById("json-container");
  
  const toggleSchemaBtn = document.getElementById("toggle-schema-btn");
  const schemaSidebar = document.getElementById("schema-sidebar");
  const schemaTree = document.getElementById("schema-tree");
  const tableCountBadge = document.getElementById("table-count");

  // Load Schema on Startup
  loadSchema();

  // Handle Form Submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return;

    // Set Loading UI
    setLoading(true);

    try {
      const response = await fetch("/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Query execution failed.");
      }

      renderResults(data);
    } catch (err) {
      renderError(err.message);
    } finally {
      setLoading(false);
    }
  });

  // Sample Chips Click Handler
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      questionInput.value = chip.dataset.question;
      questionInput.focus();
    });
  });

  // Copy SQL Handler
  copySqlBtn.addEventListener("click", () => {
    const code = sqlCode.textContent;
    navigator.clipboard.writeText(code).then(() => {
      copyBtnText.textContent = "Copied!";
      setTimeout(() => { copyBtnText.textContent = "Copy"; }, 2000);
    });
  });

  // View Toggle (Table / JSON)
  viewTableBtn.addEventListener("click", () => {
    viewTableBtn.classList.add("active");
    viewJsonBtn.classList.remove("active");
    tableContainer.classList.remove("hidden");
    jsonContainer.classList.add("hidden");
  });

  viewJsonBtn.addEventListener("click", () => {
    viewJsonBtn.classList.add("active");
    viewTableBtn.classList.remove("active");
    jsonContainer.classList.remove("hidden");
    tableContainer.classList.add("hidden");
  });

  // Schema Toggle
  toggleSchemaBtn.addEventListener("click", () => {
    schemaSidebar.classList.toggle("collapsed");
  });

  // Render Functions
  function setLoading(isLoading) {
    if (isLoading) {
      submitBtn.disabled = true;
      btnText.textContent = "Executing...";
      spinner.classList.remove("hidden");
      loadingState.classList.remove("hidden");
      resultsSection.classList.add("hidden");
    } else {
      submitBtn.disabled = false;
      btnText.textContent = "Execute Query";
      spinner.classList.add("hidden");
      loadingState.classList.add("hidden");
    }
  }

  function renderResults(data) {
    resultsSection.classList.remove("hidden");
    errorAlert.classList.add("hidden");

    // Metadata
    if (data.is_success) {
      statusBadge.textContent = "Success";
      statusBadge.className = "badge badge-success";
    } else {
      statusBadge.textContent = "Failed";
      statusBadge.className = "badge badge-danger";
    }

    // Attempts & Self-Healing Badge
    if (data.attempts > 1) {
      attemptsBadge.textContent = `Attempt ${data.attempts} (Self-Healed ⚡)`;
      attemptsBadge.className = "badge badge-success";
    } else {
      attemptsBadge.textContent = `1 Attempt`;
      attemptsBadge.className = "badge badge-outline";
    }

    // SQL Code
    sqlCode.textContent = data.sql || "-- No SQL generated --";

    // Results Array
    const results = Array.isArray(data.result) ? data.result : [];
    rowsBadge.textContent = `${results.length} rows`;

    // Render Table & JSON
    renderTable(results);
    jsonCode.textContent = JSON.stringify(results, null, 2);

    // Handle Error if any
    if (data.error) {
      errorMessage.textContent = data.error;
      errorAlert.classList.remove("hidden");
    }
  }

  function renderError(errText) {
    resultsSection.classList.remove("hidden");
    errorAlert.classList.remove("hidden");
    errorMessage.textContent = errText;
    statusBadge.textContent = "Error";
    statusBadge.className = "badge badge-danger";
    sqlCode.textContent = "-- Error encountered --";
    renderTable([]);
    jsonCode.textContent = "[]";
  }

  function renderTable(data) {
    const thead = dataTable.querySelector("thead");
    const tbody = dataTable.querySelector("tbody");
    thead.innerHTML = "";
    tbody.innerHTML = "";

    if (!data || data.length === 0) {
      tbody.innerHTML = `<tr><td style="text-align: center; color: var(--text-muted); padding: 2rem;">No rows returned</td></tr>`;
      return;
    }

    // Columns
    const columns = Object.keys(data[0]);
    const trHead = document.createElement("tr");
    columns.forEach((col) => {
      const th = document.createElement("th");
      th.textContent = col;
      trHead.appendChild(th);
    });
    thead.appendChild(trHead);

    // Rows
    data.forEach((row) => {
      const tr = document.createElement("tr");
      columns.forEach((col) => {
        const td = document.createElement("td");
        const val = row[col];
        td.textContent = val !== null && val !== undefined ? val : "NULL";
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }

  async function loadSchema() {
    try {
      const res = await fetch("/api/v1/schema");
      if (!res.ok) return;
      const data = await res.json();
      const tables = data.tables || [];

      tableCountBadge.textContent = `${tables.length} tables`;
      schemaTree.innerHTML = "";

      tables.forEach((table) => {
        const node = document.createElement("div");
        node.className = "table-node";

        const header = document.createElement("div");
        header.className = "table-header";
        header.innerHTML = `<span>📋 ${table.table_name}</span><span style="font-size:0.75rem; color:var(--text-muted);">${table.columns.length} cols</span>`;

        const colsList = document.createElement("div");
        colsList.className = "columns-list";

        table.columns.forEach((col) => {
          const colItem = document.createElement("div");
          colItem.className = "column-item";
          const pkMark = col.primary_key ? '<span class="col-pk">🔑 </span>' : '';
          colItem.innerHTML = `<span>${pkMark}${col.name}</span><span class="col-type">${col.type}</span>`;
          colsList.appendChild(colItem);
        });

        header.addEventListener("click", () => {
          colsList.style.display = colsList.style.display === "none" ? "block" : "none";
        });

        node.appendChild(header);
        node.appendChild(colsList);
        schemaTree.appendChild(node);
      });
    } catch (e) {
      schemaTree.innerHTML = '<div style="color: var(--text-muted); padding: 1rem;">Schema loading failed</div>';
    }
  }
});
