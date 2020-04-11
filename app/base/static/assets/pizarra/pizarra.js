/**
 * Pizarra
 * ------------------
 */

/**
 * fades out alerts from flash flask messages
 */
$(document).ready(function () {

    $("#flash-alert").fadeTo(3000, 500).slideUp(500, function () {
        $("#flash-alert").slideUp(500);
    });

    //doge tooltip
    $(function () {
        $('[data-toggle="popover"]').popover();
    });
    $('#doge-tooltip').popover({
        html: true
    });
    setTimeout(function () {
        $('#doge-tooltip').popover('show')
    }, 1000);
});
