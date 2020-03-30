// highlight order
$(document).ready(function() {
    $('#table tr').bind("mouseover", function() {
        const color  = $(this).contents('td').css("background-color");
        if (color === "rgb(204, 255, 204)") {
            $(this).contents('td').css("background", "rgb(176, 226, 176)");
        } else {
            $(this).contents('td').css("background", "rgba(0, 0, 0, 0.175)");
        }
        $(this).bind("mouseout", function() {
            $(this).contents('td').css("background", color);
        })
    })
});

// copy & paste values to form
function getName(obj) {
    const i = obj.className;
    document.getElementById('base').value = $(obj).parents().parents().find('#0'+i).attr('name');
    document.getElementById('rel').value = $(obj).parents().parents().find('#1'+i).attr('name');
    document.getElementById('relPrice').value = $(obj).find('td:eq(9)').text();
    document.getElementById('basePrice').value = $(obj).find('td:eq(7)').text();
    document.getElementById('baseAmount').value = $(obj).parents().parents().find('#4'+i).attr('name');
    document.getElementById('relAmount').value = $(obj).parents().parents().find('#5'+i).attr('name');
}

// confirm before cancel all orders
function cancelAll() {
    if (confirm("Cancel all open orders?")) {
        window.open("/cancel-all-orders");
    }
}

// price calculation
$('#relAmount').keyup(function() {
    const relAmount = Number($('#relAmount').val());
    const relPrice = Number($('#relPrice').val());
    document.getElementById('baseAmount').value = (relAmount / relPrice).toFixed(8);
});
$('#baseAmount').keyup(function() {
    const baseAmount  = Number($('#baseAmount').val());
    const basePrice = Number($('#basePrice').val());
    document.getElementById('relAmount').value = (baseAmount / basePrice).toFixed(8);
});
$('#relPrice').keyup(function() {
    const relAmount = Number($('#relAmount').val());
    const relPrice = Number($('#relPrice').val());
    const basePrice = 1 / relPrice;
    document.getElementById('basePrice').value = basePrice.toFixed(8);
    document.getElementById('baseAmount').value = (basePrice * relAmount).toFixed(8);
});
$('#basePrice').keyup(function() {
    const relAmount = Number($('#relAmount').val());
    const basePrice = Number($('#basePrice').val());
    document.getElementById('relPrice').value = relPrice = (1 / basePrice).toFixed(8);
    document.getElementById('baseAmount').value = (basePrice * relAmount).toFixed(8);
});

// search
let arrOfTable = []
$('#table td').each(function() {
    arrOfTable.push($(this).width());
});
let search = $('#search').val().toUpperCase();
let arrSearch = [];
let i = 0;
while (true) {
    if (search.split(" ")[i] !== undefined && search.split(" ")[i] !== "") {
        arrSearch.push(search.split(" ")[i]);
        i++;
    } else {
        break;
    }
}
if ($('#search').val() !== "") {
    $('td', '#table').closest('tr').hide();
    for (let i = 0; i < arrSearch.length; i++) {
        for (let j = 0; j < arrSearch.length; j++) {
            $('td[name="' + arrSearch[i] + arrSearch[j] + '"]', '#table').closest('tr').show();
        }
    }
    if (arrSearch.length === 1) {
        $('td[name="' + arrSearch[0] + '"]', '#table').closest('tr').show();
    }
    if (arrSearch.length === 0) {
        $('td', '#table').closest('tr').show();
    }
    i = 0;
    $('#table td').each(function() {
        $(this).css("min-width", arrOfTable[i] + "px");
        i++; 
    });
}

$('#search').keyup(function() {
    let search = $('#search').val().toUpperCase();
    let arrSearch = [];
    i = 0;
    while (true) {
        if (search.split(" ")[i] !== undefined && search.split(" ")[i] !== "") {
            arrSearch.push(search.split(" ")[i]);
            i++;
        } else {
            break;
        }
    }
    $('td', '#table').closest('tr').hide();
    for (let i = 0; i < arrSearch.length; i++) {
        for (let j = 0; j < arrSearch.length; j++) {
            $('td[name="' + arrSearch[i] + arrSearch[j] + '"]', '#table').closest('tr').show();
        }
    }
    if (arrSearch.length === 1) {
        $('td[name="' + arrSearch[0] + '"]', '#table').closest('tr').show();
    }
    if (arrSearch.length === 0) {
        $('td', '#table').closest('tr').show();
    }
    i = 0;
    $('#table td').each(function() {
        $(this).css("min-width", arrOfTable[i] + "px");
        i++; 
    });
});

// highlight cheaper orders
let socket = [];
for (let i = 0; i < $('#table tr').length; i++) {
    if (Number($('#2'+i).text()) < Number($('#'+((i+1)*(-1))).text())) {
        $('.'+i).contents('td').css("background", "#CCFFCC");
    }
}

// show only cheaper orders on button press
let showAll = true;
const addEvent = document.addEventListener ? function(target, type, action) {
    if (target) {
        target.addEventListener(type, action, false);
    }
} : function(target, type, action) {
    if (target) {
        target.attachEvent('on' + type, action, false);
    }
}
addEvent(document, 'keyup', function(e) {
    e = e || window.event;
    const key = e.which || e.keyCode;
    if (key === 13) {
        if (showAll) {
            $('td', '#table').closest('tr').hide();
            for (let i = 0; i < $('#table tr').length; i++) {
                if (Number($('#2'+i).text()) < Number($('#'+((i+1)*(-1))).text())) {
                    $('#2'+i).closest('tr').show();
                }
            }
            $('#table td').each(function() {
                $(this).css("min-width", arrOfTable[i] + "px");
                i++; 
            });
            showAll = false;
        } else {
            $('td', '#table').closest('tr').show();
            showAll = true;
        }
    }
});

// mark coin on click
function mark(obj) {
    if ($(obj).css('color') === 'rgb(68, 68, 68)') {    
        $('td[name="' + $(obj).attr('name') + '"]', '#table').css('color', 'blue');
    } else if ($(obj).css('color') === 'rgb(0, 0, 255)') {    
        $('td[name="' + $(obj).attr('name') + '"]', '#table').css('color', 'rgb(68, 68, 68)');
    }
}
