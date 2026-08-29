// Small progressive-enhancement layer: likes and comments post via fetch()
// so the feed/profile page doesn't have to fully reload. Every form still
// has a normal server-rendered fallback path (POST + redirect) if JS fails,
// since these are plain <form>/<button> elements outside of this script.

function getCsrfToken(form) {
  const input = form.querySelector('input[name="csrf_token"]');
  return input ? input.value : null;
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
