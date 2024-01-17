document.querySelector("button").addEventListener("click", () => {
    document.querySelector("input").click();
  });

  function setRating(rating) {
    // ボタンがクリックされたときに評価を設定する関数
    document.getElementById('selected-rating').value = rating;
    // すべての星をリセットして、クリックされた星までの評価を反映する
    const stars = document.querySelectorAll('.star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('selected');
        } else {
            star.classList.remove('selected');
        }
    });
}