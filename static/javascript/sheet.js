document.addEventListener('DOMContentLoaded', (event) => {
    // Hide the deleted order
    delete_order();

    // Print out order sheet
    let print_order = document.querySelector('#print');
    print_order.onclick = () => {
        print();
    }
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