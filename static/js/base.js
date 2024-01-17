(function($) {
    var $nav   = $('#navArea');
    var $btn   = $('.toggle_btn');
    var $mask  = $('#mask');
    var open   = 'open'; // class
    // menu open close
    $btn.on( 'click', function() {
      if ( ! $nav.hasClass( open ) ) {
        $nav.addClass( open );
      } else {
        $nav.removeClass( open );
      }
    });
    // mask close
    $mask.on('click', function() {
      $nav.removeClass( open );
    });
  } )(jQuery);

//開閉ボタンを押した時には
$(".open-btn1").click(function () {
  $(this).toggleClass('btnactive');//.open-btnは、クリックごとにbtnactiveクラスを付与＆除去。1回目のクリック時は付与
  $("#search-wrap").toggleClass('panelactive');//#search-wrapへpanelactiveクラスを付与
  $("#search-wrap.panelactive").fadeIn(2000);
$('#search-text').focus();//テキスト入力のinputにフォーカス
});

