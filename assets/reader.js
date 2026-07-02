/* 読書体験まわりの挙動: 文字サイズ・縦書き・夜間モード・進捗・しおり */
(function () {
  "use strict";
  var root = document.documentElement;
  var FS = ["small", "medium", "large"];

  function get(k, d) {
    try { return localStorage.getItem(k) || d; } catch (e) { return d; }
  }
  function set(k, v) {
    try { localStorage.setItem(k, v); } catch (e) { /* 私的モード等 */ }
  }

  function apply() {
    root.setAttribute("data-fontsize", get("uka-fontsize", "medium"));
    root.setAttribute("data-theme", get("uka-theme", "light"));
    root.setAttribute("data-writing", get("uka-writing", "yoko"));
    var t = document.getElementById("tool-theme");
    if (t) t.textContent = root.getAttribute("data-theme") === "dark" ? "昼" : "夜";
    var w = document.getElementById("tool-writing");
    if (w) w.textContent = root.getAttribute("data-writing") === "tate" ? "横" : "縦";
  }
  apply();

  document.addEventListener("DOMContentLoaded", function () {
    var body = document.querySelector(".novel-body");
    if (!body) return;

    function on(id, fn) {
      var el = document.getElementById(id);
      if (el) el.addEventListener("click", fn);
    }

    on("tool-fs-minus", function () {
      var i = FS.indexOf(get("uka-fontsize", "medium"));
      set("uka-fontsize", FS[Math.max(0, i - 1)]);
      apply();
    });
    on("tool-fs-plus", function () {
      var i = FS.indexOf(get("uka-fontsize", "medium"));
      set("uka-fontsize", FS[Math.min(FS.length - 1, i + 1)]);
      apply();
    });
    on("tool-theme", function () {
      set("uka-theme", get("uka-theme", "light") === "dark" ? "light" : "dark");
      apply();
    });
    on("tool-writing", function () {
      set("uka-writing", get("uka-writing", "yoko") === "tate" ? "yoko" : "tate");
      apply();
      window.scrollTo(0, 0);
      body.scrollLeft = 0;
    });

    /* ---- 進捗バーと、しおり(読了位置の保存) ---- */
    var bar = document.getElementById("reading-progress-bar");
    var posKey = "uka-pos:" + location.pathname;

    function ratio() {
      if (root.getAttribute("data-writing") === "tate") {
        var max = body.scrollWidth - body.clientWidth;
        return max > 0 ? Math.min(1, Math.abs(body.scrollLeft) / max) : 0;
      }
      var m = document.documentElement.scrollHeight - window.innerHeight;
      return m > 0 ? Math.min(1, window.scrollY / m) : 0;
    }

    var saveTimer = null;
    function onScroll() {
      var r = Math.max(0, ratio());
      if (bar) bar.style.width = (r * 100) + "%";
      clearTimeout(saveTimer);
      saveTimer = setTimeout(function () {
        set(posKey, String(r));
        set("uka-last", JSON.stringify({
          url: location.pathname,
          title: document.title.split(" | ")[0]
        }));
      }, 250);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    body.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    /* ---- 前回の続きから読むチップ ---- */
    var saved = parseFloat(get(posKey, "0"));
    if (saved > 0.05 && saved < 0.95) {
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "resume-chip";
      chip.textContent = "前回の続きから読む";
      chip.addEventListener("click", function () {
        if (root.getAttribute("data-writing") === "tate") {
          var max = body.scrollWidth - body.clientWidth;
          body.scrollLeft = -max * saved;
          if (Math.abs(body.scrollLeft) < 1) body.scrollLeft = max * saved;
        } else {
          var m = document.documentElement.scrollHeight - window.innerHeight;
          window.scrollTo(0, m * saved);
        }
        chip.remove();
      });
      document.body.appendChild(chip);
      setTimeout(function () { chip.classList.add("fade"); }, 8000);
      setTimeout(function () {
        if (chip.parentNode) chip.remove();
      }, 9200);
    }
  });
})();
