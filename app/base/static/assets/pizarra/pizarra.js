/**
 * Pizarra
 * ------------------
 */

$(document).ready(function () {

    /**
     * fades out alerts from flash flask messages
     */
    $("#flash-alert").fadeTo(5000, 500).slideUp(500, function () {
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
