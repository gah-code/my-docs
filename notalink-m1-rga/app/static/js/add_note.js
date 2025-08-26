(function(){
  const titleRow = document.getElementById('title-row');
  function sync() {
    const val = document.querySelector('input[name="category"]:checked')?.value;
    titleRow.hidden = !(val === 'literature' || val === 'permanent');
  }
  document.querySelectorAll('input[name="category"]').forEach(r => r.addEventListener('change', sync));
  sync();
})();
