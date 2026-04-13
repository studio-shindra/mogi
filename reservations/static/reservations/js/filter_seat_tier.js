(function () {
  "use strict";

  function filterSeatTiers() {
    var perfSelect = document.getElementById("id_performance");
    var tierSelect = document.getElementById("id_seat_tier");
    if (!perfSelect || !tierSelect) return;

    // 初期の全選択肢を保存
    var allOptions = [];
    for (var i = 0; i < tierSelect.options.length; i++) {
      allOptions.push({
        value: tierSelect.options[i].value,
        text: tierSelect.options[i].text,
      });
    }

    function update() {
      var perfId = perfSelect.value;
      if (!perfId) {
        // 公演未選択なら空の選択肢だけ
        tierSelect.innerHTML = "";
        var empty = document.createElement("option");
        empty.value = "";
        empty.text = "---------";
        tierSelect.appendChild(empty);
        return;
      }

      // APIから席種を取得
      fetch("/api/seat-tiers/?performance_id=" + perfId)
        .then(function (r) { return r.json(); })
        .then(function (data) {
          var currentVal = tierSelect.value;
          tierSelect.innerHTML = "";

          var empty = document.createElement("option");
          empty.value = "";
          empty.text = "---------";
          tierSelect.appendChild(empty);

          data.forEach(function (tier) {
            var opt = document.createElement("option");
            opt.value = tier.id;
            opt.text = tier.name;
            if (String(tier.id) === String(currentVal)) {
              opt.selected = true;
            }
            tierSelect.appendChild(opt);
          });
        });
    }

    perfSelect.addEventListener("change", update);

    // 新規作成時は初回もフィルタ実行
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
