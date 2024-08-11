const uploadForm = document.getElementById('upload_form');
const input_file = document.getElementById('id_upload');
const progress_bar = document.getElementById('progress');
const upload_error = document.getElementById('upload_error');

var $progress = $("#upload_progress"),
    $bar = $("#upload_progress_bar"),
    $text = $("#upload_progress_text"),
    percent = 0,
    bar_update,
    resetColors,
    orange = 30,
    yellow = 55,
    green = 85;

resetColors = function () {
    $bar
        .removeClass("progress__bar--green")
        .removeClass("progress__bar--yellow")
        .removeClass("progress__bar--orange")
        .removeClass("progress__bar--blue");

    $progress
        .removeClass("progress--complete")

};

bar_update = function (percent) {
    percent = parseFloat(percent.toFixed(1));
    upload_error.innerHTML = 'Uploading ' + percent

    $text.find("em").text(percent + "%");

    if (percent >= 100) {

        percent = 100;
        $progress.addClass("progress--complete");
        $bar.addClass("progress__bar--blue");
        $text.find("em").text("Complete");

    } else {

        if (percent >= green) {
            $bar.addClass("progress__bar--green");
        }

        else if (percent >= yellow) {
            $bar.addClass("progress__bar--yellow");
        }

        else if (percent >= orange) {
            $bar.addClass("progress__bar--orange");
        }

    }

    $bar.css({ width: percent + "%" });

};

$('#cancel_button').click(function (e) {
    window.stop();
    uploadForm.reset();
    resetColors();
    upload_error.innerHTML = 'Canceled';
    console.log('cancel_button');
    progress_bar.classList.add('not-visible');
    $progress.removeClass("progress--active");
    $("#upload_btn").removeAttr("disabled");
    return false;
});


$("#upload_form").submit(function (e) {
    $("#upload_btn").attr("disabled", true);
    e.preventDefault();
    $form = $(this)
    var formData = new FormData(this);
    const media_data = input_file.files[0];
    if (media_data != null) {
        console.log(media_data);
        progress_bar.classList.remove("not-visible");
        $progress.addClass("progress--active");
        resetColors();        
    }

    $.ajax({
        type: 'POST',
        url: 'upload_page',
        data: formData,
        dataType: 'json',
        beforeSend: function () {

        },
        xhr: function () {
            const xhr = new window.XMLHttpRequest();
            xhr.upload.addEventListener('progress', e => {
                if (e.lengthComputable) {
                    const percentProgress = (e.loaded / e.total) * 100;
                    console.log(percentProgress);
                    bar_update(percentProgress);
                    
                    // progress_bar.innerHTML = `<div class="progress-bar progress-bar-striped bg-success" 
                    // role="progressbar" style="width: ${percentProgress}%" aria-valuenow="${percentProgress}" aria-valuemin="0" 
                    // aria-valuemax="100"></div>`
                }
            });
            return xhr
        },
        success: function (response) {
            if(response.data == 'Data uploaded'){
                window.location.reload();
            }
            else{
                upload_error.innerHTML = response.data
            }
            console.log(response);
            uploadForm.reset()
            $("#upload_btn").removeAttr("disabled");
        },
        error: function (err) {
            console.log(err);
            $("#upload_btn").removeAttr("disabled");

        },
        cache: false,
        contentType: false,
        processData: false,
    });
});

