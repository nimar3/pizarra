/**
 * Pizarra
 * ------------------
 */

$(document).ready(function () {

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
