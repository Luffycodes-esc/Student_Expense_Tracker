# =============================================================================
# Student Expense Tracker — Flask + Flask-SQLAlchemy + SQLite
# =============================================================================
# HOW THE DATABASE CONNECTION IS INITIALIZED:
#   1. We create a Flask app instance.
#   2. We configure `SQLALCHEMY_DATABASE_URI` to point at a local SQLite file
#      called `expenses.db`.  SQLite needs no separate server process; the file
#      is created automatically the first time the app runs.
#   3. We pass the app to `SQLAlchemy(app)` — this binds the extension to our
#      Flask application and sets up the connection pool internally.
#   4. Inside `if __name__ == "__main__"` we call `db.create_all()` (inside an
#      app-context) to create every table defined by our models if they do not
#      already exist.
# =============================================================================

from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

# ---------------------------------------------------------------------------
# App & DB initialisation
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Tell SQLAlchemy to use a SQLite file named `expenses.db` in the project root.
# The `///` prefix means a *relative* path; use `////abs/path` for absolute.
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses.db"

# Disable the modification-tracking overhead (not needed here, saves memory).
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Bind the SQLAlchemy extension to our Flask application.
# This internally creates the engine and session factory.
db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class Expense(db.Model):
    """Represents a single student expense row in the database."""

    id       = db.Column(db.Integer,     primary_key=True)
    item     = db.Column(db.String(120), nullable=False)
    amount   = db.Column(db.Float,       nullable=False)
    # category is restricted to 'Need' or 'Want' at the application layer
    category = db.Column(db.String(10),  nullable=False)

    def to_dict(self):
        return {
            "id":       self.id,
            "item":     self.item,
            "amount":   self.amount,
            "category": self.category,
        }


# ---------------------------------------------------------------------------
# Inline HTML template (keeps everything in one file)
# ---------------------------------------------------------------------------

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Student Expense Tracker</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:ital,wght@0,300;0,600;1,300&display=swap" rel="stylesheet"/>
  <style>
    /* ── reset & tokens ─────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #f5f0e8;
      --surface:   #fffdf7;
      --border:    #d6cfc0;
      --text:      #1a1714;
      --muted:     #7a7060;
      --need:      #2d6a4f;
      --want:      #c8523a;
      --accent:    #b5803c;
      --radius:    6px;
    }

    body {
      font-family: 'DM Mono', monospace;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem 1rem 4rem;
    }

    /* ── layout ──────────────────────────────────────────── */
    .wrapper {
      max-width: 760px;
      margin: 0 auto;
    }

    header {
      border-bottom: 1px solid var(--border);
      padding-bottom: 1.25rem;
      margin-bottom: 2.5rem;
    }

    header h1 {
      font-family: 'Fraunces', serif;
      font-weight: 600;
      font-size: clamp(1.6rem, 4vw, 2.4rem);
      letter-spacing: -0.02em;
      line-height: 1.1;
    }

    header p {
      font-size: 0.78rem;
      color: var(--muted);
      margin-top: 0.3rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    /* ── stats bar ───────────────────────────────────────── */
    .stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
      margin-bottom: 2.5rem;
    }

    .stat-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1rem 1.2rem;
    }

    .stat-card .label {
      font-size: 0.68rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 0.4rem;
    }

    .stat-card .value {
      font-family: 'Fraunces', serif;
      font-size: 1.6rem;
      font-weight: 300;
    }

    .stat-card.want .value { color: var(--want); }
    .stat-card.need .value { color: var(--need); }

    /* ── add-expense form ────────────────────────────────── */
    .add-form {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.5rem;
      margin-bottom: 2.5rem;
    }

    .add-form h2 {
      font-family: 'Fraunces', serif;
      font-weight: 300;
      font-size: 1.1rem;
      margin-bottom: 1.1rem;
      color: var(--muted);
    }

    .fields {
      display: grid;
      grid-template-columns: 2fr 1fr 1fr auto;
      gap: 0.7rem;
      align-items: end;
    }

    @media (max-width: 560px) {
      .fields { grid-template-columns: 1fr 1fr; }
      .fields button { grid-column: span 2; }
    }

    label { display: block; }
    .field-label {
      font-size: 0.65rem;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 0.3rem;
    }

    input, select {
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 0.55rem 0.75rem;
      font-family: 'DM Mono', monospace;
      font-size: 0.85rem;
      color: var(--text);
      outline: none;
      transition: border-color .18s;
    }

    input:focus, select:focus {
      border-color: var(--accent);
    }

    button {
      background: var(--text);
      color: var(--bg);
      border: none;
      border-radius: var(--radius);
      padding: 0.6rem 1.2rem;
      font-family: 'DM Mono', monospace;
      font-size: 0.8rem;
      letter-spacing: 0.04em;
      cursor: pointer;
      transition: opacity .18s;
      white-space: nowrap;
    }

    button:hover { opacity: 0.75; }

    /* ── expense table ───────────────────────────────────── */
    .table-wrap {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.84rem;
    }

    thead tr {
      background: var(--bg);
      border-bottom: 1px solid var(--border);
    }

    th {
      padding: 0.7rem 1rem;
      text-align: left;
      font-size: 0.65rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      font-weight: 500;
    }

    td {
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--border);
    }

    tr:last-child td { border-bottom: none; }

    .badge {
      display: inline-block;
      padding: 0.18rem 0.55rem;
      border-radius: 99px;
      font-size: 0.68rem;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      font-weight: 500;
    }

    .badge.Need { background: #d8f3e8; color: var(--need); }
    .badge.Want { background: #fde8e4; color: var(--want); }

    /* ── action buttons ──────────────────────────────────── */
    .btn-action {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.28rem 0.65rem;
      border-radius: var(--radius);
      font-family: 'DM Mono', monospace;
      font-size: 0.72rem;
      font-weight: 500;
      letter-spacing: 0.03em;
      cursor: pointer;
      border: 1px solid transparent;
      transition: opacity .15s, transform .1s;
      text-decoration: none;
    }
    .btn-action:active { transform: scale(.96); }
    .btn-action:hover  { opacity: .75; }

    /* Toggle: outlined in the current-category colour */
    .btn-toggle-need {
      background: #d8f3e8;
      color: var(--need);
      border-color: #a8dfc3;
    }
    .btn-toggle-want {
      background: #fde8e4;
      color: var(--want);
      border-color: #f5bfb4;
    }

    /* Delete: soft red */
    .btn-delete {
      background: #fde8e4;
      color: #9b2a1a;
      border-color: #f5bfb4;
    }

    .actions-cell {
      display: flex;
      gap: 0.45rem;
      align-items: center;
    }

    .empty {
      text-align: center;
      padding: 2.5rem;
      color: var(--muted);
      font-size: 0.82rem;
      font-style: italic;
    }

    /* ── flash ───────────────────────────────────────────── */
    #flash {
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      background: var(--text);
      color: var(--bg);
      padding: 0.7rem 1.2rem;
      border-radius: var(--radius);
      font-size: 0.8rem;
      opacity: 0;
      transform: translateY(6px);
      transition: opacity .3s, transform .3s;
      pointer-events: none;
    }

    #flash.show {
      opacity: 1;
      transform: translateY(0);
    }
  </style>
</head>
<body>
  <div class="wrapper">

    <header>
      <h1>Expense Tracker</h1>
      <p>Track your needs &amp; wants · stay on budget</p>
    </header>

    <!-- Stats -->
    <div class="stats">
      <div class="stat-card">
        <div class="label">Total Expenses</div>
        <div class="value">{{ expenses | length }}</div>
      </div>
      <div class="stat-card need">
        <div class="label">Total Spent</div>
        <div class="value">₹{{ "%.2f" | format(total) }}</div>
      </div>
      <div class="stat-card want">
        <div class="label">Wants Total</div>
        <div class="value">₹{{ "%.2f" | format(wants_total) }}</div>
      </div>
    </div>

    <!-- Add Form -->
    <div class="add-form">
      <h2>+ Add Expense</h2>
      <div class="fields" id="addForm">
        <label>
          <span class="field-label">Item</span>
          <input type="text" id="item" placeholder="e.g. Textbook" />
        </label>
        <label>
          <span class="field-label">Amount (₹)</span>
          <input type="number" id="amount" placeholder="0.00" min="0" step="0.01" />
        </label>
        <label>
          <span class="field-label">Category</span>
          <select id="category">
            <option value="Need">Need</option>
            <option value="Want">Want</option>
          </select>
        </label>
        <button onclick="addExpense()">Add</button>
      </div>
    </div>

    <!-- Table -->
    <div class="table-wrap">
      <table id="expenseTable">
        <thead>
          <tr>
            <th>#</th>
            <th>Item</th>
            <th>Amount</th>
            <th>Category</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% if expenses %}
            {% for e in expenses %}
            <tr>
              <td style="color:var(--muted)">{{ e.id }}</td>
              <td>{{ e.item }}</td>
              <td>₹{{ "%.2f" | format(e.amount) }}</td>
              <td><span class="badge {{ e.category }}">{{ e.category }}</span></td>
              <td>
                <div class="actions-cell">
                  <!--
                    Toggle button: clicking calls /toggle/<id> via fetch.
                    The label and style reflect the CURRENT category so the
                    user knows what will change.
                  -->
                  <button
                    class="btn-action btn-toggle-{{ e.category | lower }}"
                    onclick="toggleCategory({{ e.id }}, this)">
                    ⇄ {{ "→ Want" if e.category == "Need" else "→ Need" }}
                  </button>

                  <!--
                    Delete button: calls /delete/<id> via fetch, then removes
                    the row from the DOM so no full-page reload is needed.
                  -->
                  <button
                    class="btn-action btn-delete"
                    onclick="deleteExpense({{ e.id }}, this)">
                    ✕ Delete
                  </button>
                </div>
              </td>
            </tr>
            {% endfor %}
          {% else %}
            <tr><td colspan="5" class="empty">No expenses yet — add your first one above.</td></tr>
          {% endif %}
        </tbody>
      </table>
    </div>

  </div>

  <div id="flash"></div>

  <script>
    async function addExpense() {
      const item     = document.getElementById('item').value.trim();
      const amount   = parseFloat(document.getElementById('amount').value);
      const category = document.getElementById('category').value;

      if (!item || isNaN(amount) || amount <= 0) {
        flash('Please fill in a valid item and amount.');
        return;
      }

      const res = await fetch('/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item, amount, category })
      });

      const data = await res.json();
      if (data.success) {
        flash('Expense added!');
        setTimeout(() => location.reload(), 600);
      } else {
        flash(data.error || 'Something went wrong.');
      }
    }

    // ── Toggle category (Need ↔ Want) ──────────────────────────────────────
    // Sends a GET to /toggle/<id>. On success the backend returns the new
    // category; we update the badge and button in-place without a page reload.
    async function toggleCategory(id, btn) {
      btn.disabled = true;
      const res  = await fetch(`/toggle/${id}`, { method: 'POST' });
      const data = await res.json();

      if (!data.success) {
        flash(data.error || 'Toggle failed.');
        btn.disabled = false;
        return;
      }

      const newCat = data.category;           // "Need" or "Want"
      const row    = btn.closest('tr');

      // Update the category badge
      const badge = row.querySelector('.badge');
      badge.textContent = newCat;
      badge.className   = `badge ${newCat}`;

      // Swap button style & label to reflect the new state
      btn.className = `btn-action btn-toggle-${newCat.toLowerCase()}`;
      btn.textContent = `⇄ → ${newCat === 'Need' ? 'Want' : 'Need'}`;
      btn.disabled    = false;

      flash(`Switched to ${newCat}`);
    }

    // ── Delete expense ─────────────────────────────────────────────────────
    // Sends a POST to /delete/<id>. On success the <tr> is removed from the
    // DOM immediately; the server has already committed the deletion.
    async function deleteExpense(id, btn) {
      if (!confirm('Delete this expense?')) return;
      btn.disabled = true;

      const res  = await fetch(`/delete/${id}`, { method: 'POST' });
      const data = await res.json();

      if (!data.success) {
        flash(data.error || 'Delete failed.');
        btn.disabled = false;
        return;
      }

      // Animate row out, then remove it
      const row = btn.closest('tr');
      row.style.transition = 'opacity .25s';
      row.style.opacity    = '0';
      setTimeout(() => row.remove(), 260);
      flash('Expense deleted.');
    }

    function flash(msg) {
      const el = document.getElementById('flash');
      el.textContent = msg;
      el.classList.add('show');
      setTimeout(() => el.classList.remove('show'), 2600);
    }
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """
    Main route: fetch all expenses, compute the 'Want' subtotal via an
    aggregated SQLAlchemy query, then render the dashboard.
    """
    # Fetch every expense row ordered by newest first
    expenses = Expense.query.order_by(Expense.id.desc()).all()

    # Aggregate sum of amounts where category == 'Want' directly in SQLite.
    # func.sum() maps to SQL's SUM(); the [0] unpacks the single-row result.
    wants_total = (
        db.session.query(func.sum(Expense.amount))
        .filter(Expense.category == "Want")
        .scalar() or 0.0
    )

    total = sum(e.amount for e in expenses)

    return render_template_string(
        TEMPLATE,
        expenses=expenses,
        wants_total=wants_total,
        total=total,
    )


@app.route("/add", methods=["POST"])
def add_expense():
    """
    POST /add — accepts JSON body: { item, amount, category }
    Validates input, creates an Expense row, commits to the DB, and returns
    a JSON acknowledgement.
    """
    data = request.get_json(silent=True) or {}

    item     = (data.get("item") or "").strip()
    amount   = data.get("amount")
    category = (data.get("category") or "").strip()

    # --- validation ---------------------------------------------------------
    if not item:
        return jsonify({"success": False, "error": "Item name is required."}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Amount must be a positive number."}), 400

    if category not in ("Need", "Want"):
        return jsonify({"success": False, "error": "Category must be 'Need' or 'Want'."}), 400

    # --- persist ------------------------------------------------------------
    expense = Expense(item=item, amount=amount, category=category)
    db.session.add(expense)
    db.session.commit()

    return jsonify({"success": True, "expense": expense.to_dict()}), 201


@app.route("/delete/<int:id>", methods=["POST"])
def delete_expense(id):
    """
    POST /delete/<id> — permanently removes the Expense row with the given
    primary key from the database.

    HOW db.session.commit() IS USED:
      1. db.session.delete(expense) marks the object for deletion in
         SQLAlchemy's Unit-of-Work tracker — nothing is sent to SQLite yet.
      2. db.session.commit() flushes the pending DELETE statement to SQLite
         and commits the transaction.  Without this call the deletion would
         be rolled back when the session closes.
    """
    # get_or_404 queries by primary key and automatically returns a 404
    # response if no matching row exists — no manual check needed.
    expense = db.get_or_404(Expense, id)

    db.session.delete(expense)   # Stage the DELETE in the session
    db.session.commit()          # Persist: writes DELETE to SQLite

    return jsonify({"success": True, "deleted_id": id})


@app.route("/toggle/<int:id>", methods=["POST"])
def toggle_category(id):
    """
    POST /toggle/<id> — flips the category of the given Expense between
    'Need' and 'Want' and persists the change.

    HOW db.session.commit() IS USED:
      1. We mutate expense.category directly on the ORM object.
         SQLAlchemy's change-tracking detects the mutation automatically.
      2. db.session.commit() flushes the pending UPDATE statement to SQLite
         and commits the transaction.  The column value in expenses.db is now
         permanently changed.
    """
    expense = db.get_or_404(Expense, id)

    # Flip the category
    expense.category = "Want" if expense.category == "Need" else "Need"

    # No db.session.add() needed — SQLAlchemy already tracks the loaded object.
    db.session.commit()          # Persist: writes UPDATE to SQLite

    return jsonify({"success": True, "expense": expense.to_dict(),
                    "category": expense.category})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # An application context is required for SQLAlchemy operations outside of
    # a request. `with app.app_context()` pushes one so `db.create_all()` can
    # inspect the app's configuration and create the tables in `expenses.db`.
    with app.app_context():
        db.create_all()   # Creates `expense` table if it doesn't exist yet

    app.run(debug=True)
