/* Chart.js glue: every <canvas data-chart="#json-id"> is drawn from the JSON
   the server rendered next to it (same chart types as the Recharts version:
   bar, horizontal bar, pie). Values are whole shillings for geometry only;
   tooltips use the same "UGX 1,234" formatting as the tables. */
(function () {
  "use strict";
  function css(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  function ugx(v) { return "UGX " + Math.round(v).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ","); }
  function draw(root) {
    (root || document).querySelectorAll("canvas[data-chart]").forEach(function (canvas) {
      if (canvas._chart) canvas._chart.destroy();
      var spec = JSON.parse(document.querySelector(canvas.dataset.chart).textContent);
      var colors = (spec.colors || []).map(function (c) { return c.charAt(0) === "-" ? css(c) : c; });
      var color = spec.color ? (spec.color.charAt(0) === "-" ? css(spec.color) : spec.color) : css("--primary");
      var data = {
        labels: spec.labels,
        datasets: [{ label: spec.label || "", data: spec.values, backgroundColor: colors.length ? colors : color }],
      };
      var opts = { responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false } } };
      if (spec.money) opts.plugins.tooltip = { callbacks: { label: function (c) { return ugx(c.parsed.y !== undefined && spec.type !== "pie" ? (spec.horizontal ? c.parsed.x : c.parsed.y) : c.parsed); } } };
      if (spec.type === "pie") {
        opts.plugins.legend = { display: true, position: "bottom", labels: { font: { size: 11 } } };
      } else {
        opts.indexAxis = spec.horizontal ? "y" : "x";
        opts.scales = { x: { ticks: { font: { size: 11 }, precision: 0 }, grid: { borderDash: [3, 3] } }, y: { ticks: { font: { size: 11 }, precision: 0 } } };
      }
      canvas._chart = new Chart(canvas, { type: spec.type === "pie" ? "pie" : "bar", data: data, options: opts });
    });
  }
  document.addEventListener("DOMContentLoaded", function () { draw(document); });
  document.addEventListener("htmx:afterSettle", function (e) { draw(e.detail.target); });
})();
