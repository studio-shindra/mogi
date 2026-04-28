(function () {
  "use strict";

  var TIER_SELECT_IDS = [
    "id_seat_tier",
    "id_first_choice_seat_tier",
    "id_second_choice_seat_tier",
  ];

  function setEmpty(sel) {
    sel.innerHTML = "";
    var empty = document.createElement("option");
    empty.value = "";
    empty.text = "---------";
    sel.appendChild(empty);
  }

  function applyTiers(sel, tiers) {
    var currentVal = sel.value;
    sel.innerHTML = "";
    var empty = document.createElement("option");
    empty.value = "";
    empty.text = "---------";
    sel.appendChild(empty);
    tiers.forEach(function (tier) {
      var opt = document.createElement("option");
      opt.value = tier.id;
      opt.text = tier.name;
      if (String(tier.id) === String(currentVal)) {
        opt.selected = true;
      }
      sel.appendChild(opt);
    });
  }

  function filterSeatTiers() {
    var perfSelect = document.getElementById("id_performance");
    if (!perfSelect) return;

    var tierSelects = TIER_SELECT_IDS
      .map(function (id) { return document.getElementById(id); })
      .filter(Boolean);
    if (!tierSelects.length) return;

    function update() {
      var perfId = perfSelect.value;
      if (!perfId) {
        tierSelects.forEach(setEmpty);
        return;
      }
      fetch("/api/seat-tiers/?performance_id=" + perfId)
        .then(function (r) { return r.json(); })
        .then(function (data) {
          tierSelects.forEach(function (sel) { applyTiers(sel, data); });
        });
    }

    perfSelect.addEventListener("change", update);

    if (perfSelect.value) {
      update();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", filterSeatTiers);
  } else {
    filterSeatTiers();
  }
})();
