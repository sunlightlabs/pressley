jQuery(document).ready(function($){

    var $expand_buttons = $(".expand-button");
    $expand_buttons.button();
    $expand_buttons.click(function(event){
        var $btn = $(this);
        var $detail_container = $(".fail-detail-container", $btn.parent());
        $detail_container.toggle('blind', {}, 'fast');
        $btn_text = $(".ui-button-text", $btn);
        $btn_text.text(($btn_text.text() === '+') ? '-' : '+');
    });
        
});

