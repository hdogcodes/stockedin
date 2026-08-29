// Small progressive-enhancement layer: likes and comments post via fetch()
// so the feed/profile page doesn't have to fully reload. Every form still
// has a normal server-rendered fallback path (POST + redirect) if JS fails,
// since these are plain <form>/<button> elements outside of this script.

function getCsrfToken(form) {
  const input = form.querySelector('input[name="csrf_token"]');
  return input ? input.value : null;
}

const tickerInput = document.getElementById("ticker-input");
if (tickerInput) {
  const suggestionsList = document.getElementById("ticker-suggestions");
  let debounceTimer = null;
  let activeIndex = -1;
  let currentResults = [];
  let requestId = 0;

  function closeSuggestions() {
    suggestionsList.hidden = true;
    suggestionsList.innerHTML = "";
    currentResults = [];
    activeIndex = -1;
  }

  function renderSuggestions(results) {
    currentResults = results;
    activeIndex = -1;
    suggestionsList.innerHTML = "";

    if (results.length === 0) {
      closeSuggestions();
      return;
    }

    results.forEach((item) => {
      const li = document.createElement("li");
      li.className = "ticker-suggestion";
      li.setAttribute("role", "option");
      const symbol = document.createElement("span");
      symbol.className = "ticker-suggestion-symbol";
      symbol.textContent = item.symbol;
      const desc = document.createElement("span");
      desc.className = "ticker-suggestion-desc";
      desc.textContent = item.description;
      li.append(symbol, desc);
      li.addEventListener("mousedown", (event) => {
        // mousedown (not click) fires before the input's blur handler closes the list.
        event.preventDefault();
        tickerInput.value = item.symbol;
        closeSuggestions();
      });
      suggestionsList.appendChild(li);
    });

    suggestionsList.hidden = false;
  }

  function highlight(index) {
    const items = suggestionsList.querySelectorAll(".ticker-suggestion");
    items.forEach((el, i) => el.classList.toggle("active", i === index));
    if (index >= 0 && items[index]) {
      items[index].scrollIntoView({ block: "nearest" });
    }
  }

  tickerInput.addEventListener("input", () => {
    const query = tickerInput.value.trim();
    clearTimeout(debounceTimer);

    if (query.length < 2) {
      closeSuggestions();
      return;
    }

    debounceTimer = setTimeout(async () => {
      const thisRequest = ++requestId;
      try {
        const response = await fetch(`/api/ticker-search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error("ticker search failed");
        const results = await response.json();
        if (thisRequest !== requestId) return; // a newer keystroke superseded this request
        renderSuggestions(results);
      } catch (err) {
        console.error(err);
      }
    }, 250);
  });

  tickerInput.addEventListener("keydown", (event) => {
    if (suggestionsList.hidden || currentResults.length === 0) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      activeIndex = Math.min(activeIndex + 1, currentResults.length - 1);
      highlight(activeIndex);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      activeIndex = Math.max(activeIndex - 1, 0);
      highlight(activeIndex);
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      tickerInput.value = currentResults[activeIndex].symbol;
      closeSuggestions();
    } else if (event.key === "Escape") {
      closeSuggestions();
    }
  });

  tickerInput.addEventListener("blur", closeSuggestions);
}

const friendSearch = document.getElementById("friend-search");
if (friendSearch) {
  const rows = Array.from(document.querySelectorAll("#friend-list .user-row"));
  const emptyState = document.getElementById("friend-search-empty");

  friendSearch.addEventListener("input", () => {
    const query = friendSearch.value.trim().toLowerCase();
    let visibleCount = 0;

    rows.forEach((row) => {
      const matches = row.dataset.username.includes(query);
      row.hidden = !matches;
      if (matches) visibleCount += 1;
    });

    if (emptyState) emptyState.hidden = visibleCount !== 0;
  });
}

document.addEventListener("click", async (event) => {
  const btn = event.target.closest(".like-btn");
  if (!btn) return;

  const portfolioId = btn.dataset.portfolioId;
  const card = document.getElementById(`portfolio-${portfolioId}`);
  const csrfInput = card.querySelector('.comment-form input[name="csrf_token"]');
  const csrfToken = csrfInput ? csrfInput.value : null;

  btn.disabled = true;
  try {
    const response = await fetch(`/portfolio/${portfolioId}/like`, {
      method: "POST",
      headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
    });
    if (!response.ok) throw new Error("like request failed");
    const data = await response.json();

    btn.classList.toggle("liked", data.liked);
    btn.dataset.liked = data.liked ? "true" : "false";
    btn.querySelector(".like-count").textContent = data.like_count;
  } catch (err) {
    console.error(err);
  } finally {
    btn.disabled = false;
  }
});

document.addEventListener("submit", async (event) => {
  const form = event.target.closest(".comment-form");
  if (!form) return;

  event.preventDefault();
  const portfolioId = form.dataset.portfolioId;
  const textarea = form.querySelector("textarea");
  const errorEl = form.querySelector(".comment-error");
  const csrfToken = getCsrfToken(form);

  errorEl.hidden = true;

  try {
    const response = await fetch(`/portfolio/${portfolioId}/comment`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      },
      body: new URLSearchParams({
        csrf_token: csrfToken || "",
        body: textarea.value,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      errorEl.textContent = data.error || "Could not post comment.";
      errorEl.hidden = false;
      return;
    }

    const list = form.closest(".comments").querySelector(".comment-list");
    const li = document.createElement("li");
    li.className = "comment";
    li.innerHTML = `
      <a href="/user/${data.username}">${data.username}</a>
      <span class="comment-body"></span>
      <span class="comment-date">${data.created_at}</span>
    `;
    li.querySelector(".comment-body").textContent = data.body;
    list.appendChild(li);

    textarea.value = "";
  } catch (err) {
    errorEl.textContent = "Network error — please try again.";
    errorEl.hidden = false;
    console.error(err);
  }
});
