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
});