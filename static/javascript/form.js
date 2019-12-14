// datepicker
$(function() {
    $( "#datepicker" ).datepicker();
});

// JavaScript for disabling form submissions if there are invalid fields
(function() {
  'use strict';
    window.addEventListener('load', function() {
        // Fetch all the forms we want to apply custom Bootstrap validation styles to
        var forms = document.getElementsByClassName('needs-validation');
        // Loop over them and prevent submission
        var validation = Array.prototype.filter.call(forms, function(form) {
            form.addEventListener('submit', function(event) {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                }
            form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();

window.addEventListener("DOMContentLoaded", (event) => {
    // JavaScript to change time according to different sessions
    document.getElementById("noon").onchange = change2noontime;
    document.getElementById("night").onchange = change2nighttime;

    // Ensure date is valid
    // let datepicker = document.querySelector("input[name='datepicker']")
    
    // datepicker.onchange = (event) => {
    //     $.get('/checkdatepicker?datepicker=' + datepicker.value, (validation) => {
    //         if (validation === false) {
    //             console.log(validation);
    //             document.querySelector("input[name='datepicker'] + div").innerHTML = "輸入日期小於今天";
    //             datepicker.classList.add('was-validated');
    //         }
    //     })
    // }
})

function change2noontime() {
    let noon_time = ['11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00'];
    if (document.getElementById("noon").value)
    {
        document.getElementById("time").innerHTML = "<option disabled selected value=''>請選擇時間</option>";
        for (let time of noon_time)
        {
            document.getElementById("time").innerHTML += '<option>' + time + '</option>';
        }
    }
}

function change2nighttime() {
    let night_time = ['17:00', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00'];
    if (document.getElementById("night").value)
    {
        document.getElementById("time").innerHTML = "<option disabled selected value=''>請選擇時間</option>";
        for (let time of night_time)
        {
            document.getElementById("time").innerHTML += '<option>' + time + '</option>';
        }
    }
}
