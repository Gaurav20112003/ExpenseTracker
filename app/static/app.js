const expenseForm = document.querySelector("#expense-form");
const expenseInput = document.querySelector("#expense-text");
const dateFilter = document.querySelector("#date-filter");
const expenseList = document.querySelector("#expense-list");
const notice = document.querySelector("#notice");
const submitButton = expenseForm.querySelector("button");

function showNotice(message, isError = false) {
  notice.textContent = message;
  notice.classList.toggle("notice-error", isError);
  notice.hidden = !message;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const error = await response.json();
      if (typeof error.detail === "string") {
        message = error.detail;
      }
    } catch {
      // Keep the HTTP status message when the server does not return JSON.
    }
    throw new Error(message);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function createTextElement(tagName, className, text) {
  const element = document.createElement(tagName);
  element.className = className;
  element.textContent = text;
  return element;
}

function formatAmount(amount, currency) {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
    }).format(amount);
  } catch {
    return `${currency} ${Number(amount).toFixed(2)}`;
  }
}

function renderExpenses(expenses) {
  expenseList.replaceChildren();

  if (expenses.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.append(
      createTextElement("span", "empty-icon", "-"),
      createTextElement("h3", "", "No expenses found"),
      createTextElement(
        "p",
        "",
        dateFilter.value
          ? "Try another date or clear the filter."
          : "Your expenses will show up here once you add one.",
      ),
    );
    expenseList.append(empty);
    return;
  }

  const groups = new Map();
  for (const expense of expenses) {
    if (!groups.has(expense.date)) {
      groups.set(expense.date, []);
    }
    groups.get(expense.date).push(expense);
  }

  for (const [day, dayExpenses] of groups) {
    const group = document.createElement("section");
    group.className = "day-group";
    const heading = document.createElement("div");
    heading.className = "day-heading";
    heading.append(
      createTextElement("h3", "", new Date(`${day}T12:00:00`).toLocaleDateString(
        undefined,
        { weekday: "long", month: "long", day: "numeric", year: "numeric" },
      )),
      createTextElement("span", "day-count", `${dayExpenses.length} ${dayExpenses.length === 1 ? "expense" : "expenses"}`),
    );
    group.append(heading);

    for (const expense of dayExpenses) {
      const item = document.createElement("article");
      item.className = "expense-item";
      const category = createTextElement("span", "category-icon", expense.category.slice(0, 1));
      category.setAttribute("aria-hidden", "true");

      const details = document.createElement("div");
      details.className = "expense-details";
      details.append(
        createTextElement("h4", "", expense.merchant || expense.description),
        createTextElement("p", "", expense.description),
      );

      const timestamp = new Date(expense.created_at);
      const timeText = Number.isNaN(timestamp.getTime())
        ? ""
        : timestamp.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
      const meta = createTextElement(
        "span",
        "expense-time",
        timeText ? `${expense.category} | Added ${timeText}` : expense.category,
      );
      details.append(meta);

      const trailing = document.createElement("div");
      trailing.className = "expense-trailing";
      trailing.append(
        createTextElement("strong", "expense-amount", formatAmount(expense.amount, expense.currency)),
      );
      const deleteButton = createTextElement("button", "delete-button", "Delete");
      deleteButton.type = "button";
      deleteButton.setAttribute("aria-label", `Delete ${expense.merchant || expense.description}`);
      deleteButton.addEventListener("click", () => deleteExpense(expense));
      trailing.append(deleteButton);

      item.append(category, details, trailing);
      group.append(item);
    }
    expenseList.append(group);
  }
}

async function loadExpenses() {
  showNotice("");
  expenseList.setAttribute("aria-busy", "true");
  try {
    const query = dateFilter.value
      ? `?expense_day=${encodeURIComponent(dateFilter.value)}`
      : "";
    const expenses = await requestJson(`/api/v1/expenses${query}`);
    renderExpenses(expenses);
    return true;
  } catch (error) {
    showNotice(error.message, true);
    return false;
  } finally {
    expenseList.removeAttribute("aria-busy");
  }
}

async function deleteExpense(expense) {
  const label = expense.merchant || expense.description;
  if (!window.confirm(`Delete "${label}" from your expense history?`)) {
    return;
  }
  try {
    await requestJson(`/api/v1/expenses/${expense.id}`, { method: "DELETE" });
    if (await loadExpenses()) {
      showNotice("Expense deleted.");
    }
  } catch (error) {
    showNotice(error.message, true);
  }
}

expenseForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!expenseForm.reportValidity()) {
    return;
  }

  submitButton.disabled = true;
  submitButton.querySelector("span:first-child").textContent = "Saving...";
  showNotice("");
  try {
    await requestJson("/api/v1/expenses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: expenseInput.value.trim() }),
    });
    expenseInput.value = "";
    dateFilter.value = "";
    if (await loadExpenses()) {
      showNotice("Expense saved.");
    }
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span:first-child").textContent = "Add expense";
  }
});

dateFilter.addEventListener("change", loadExpenses);
loadExpenses();
