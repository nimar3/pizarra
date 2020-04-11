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


    $("#profile-tabs li").click(function () {
        if ($(this).attr('id') === 'profile-tabs-badges') {
            setTimeout(function () {
                $('#doge-tooltip').popover('show')
            }, 1000);
        } else {
            $('#doge-tooltip').popover('hide')
        }
    });
});
