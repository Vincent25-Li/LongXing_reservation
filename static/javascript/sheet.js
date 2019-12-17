document.addEventListener('DOMContentLoaded', (event) => {
    // Hide the deleted order
    delete_order();

    // Print out order sheet
    let print_order = document.querySelector('#print');
    print_order.onclick = () => {
        print();
    }

    // change the order list when selected
    let date = document.querySelector('#datepicker');
    let sections = document.querySelectorAll('input[name="section"]');
    date.onchange = select_orders;
    sections.forEach(section => {
        section.onchange = select_orders;
    })
})

// Hide the deleted order
function delete_order() {
    document.querySelectorAll('.delete_order').forEach((button) => {
        button.onclick = () => {
            let id = button.dataset.id;
            let confirmation = confirm("確認刪除此預訂");
            if (confirmation) 
            {
                $.get('/longxing/deleteorder/' + id, function(data) {
                    document.querySelector("tbody").innerHTML = data;
                    delete_order();
                })
            }  
        }
    })
}

// Update order list from server
function select_orders() {
    
    let select_date = document.querySelector('#datepicker').value;
    let select_section = document.querySelector('input[name="section"]:checked').value;
    $.get(`/longxing/sheetselected?date=${select_date}&section=${select_section}`, data => {
        document.querySelector("tbody").innerHTML = data;

        delete_order()
    })
}