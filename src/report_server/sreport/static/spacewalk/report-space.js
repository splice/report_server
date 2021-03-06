/* 
Copyright  2012 Red Hat, Inc.
This software is licensed to you under the GNU General Public
License as published by the Free Software Foundation; either version
2 of the License (GPLv2) or (at your option) any later version.
There is NO WARRANTY for this software, express or implied,
including the implied warranties of MERCHANTABILITY,
NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
have received a copy of GPLv2 along with this software; if not, see
http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
*/

var first_logged_in = false;
var logged_in = false;
var is_admin = true;
var csrftoken = null;
var pxt = null;
var page_size = 10; // default value
var color_green = "#99BF5E"
var color_red = "#CA0010"
var color_yellow = "#F1E95E"

$(document).ready(function() {
    csrftoken = getCookie('csrftoken');
    
    $("#spinner").bind("ajaxSend", function() {
		$(this).show();
		
	}).bind("ajaxStop", function() {
		$(this).hide();
	}).bind("ajaxError", function() {
		$(this).hide();
	});
    
	hide_pages();
    setupLoginForm();
    setupLoginButtons();
    //setupCreateForm();
    //setupCreateDatesForm();
    openCreateLogin();
    navButtonDocReady();
    form_filter_link_hide(false);
    if (logged_in){
        $('#login-button').hide();
        filterInitialPopulate();
        //document.getElementById("account-button-span").innerHTML = "Account: " + rtn.username;
    }    

});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}




function drawCircle(element_selector, color_choice, width) {
    //Following approach Katello/SAM use for rendering colored 'ball' for dashboard
    //https://github.com/Katello/katello/blob/master/src/app/views/dashboard/_subscriptions.haml
    //https://github.com/Katello/katello/blob/master/src/app/stylesheets/sections/dashboard.scss
    //https://github.com/Katello/katello/blob/master/src/public/javascripts/dashboard.js#L17
    var plot_data = [{data:1, color:color_choice}];
    var elem = $(element_selector);
    if (elem.length == 0) {
        alert("Couldn't find selector with: " + element_selector);
        return;
    }
    $.plot(elem, plot_data, {
        series: {
            pie:{
                show: true,
                radius: width,
                label: {
                    show: false
                }
            }
        },
        legend: {
            show: false
        }
    });
}


function populateReport(rtn) {
    var pane = $('#report_pane');
    if ($("div.status_icon").length) {
        // Attempting to work around 'flot' issue of:
        // Uncaught TypeError: Cannot call method 'shutdown' of undefined
        // Issue is that flot will attempt to 'reuse' the existing DOM element if it exists
        // We ran into an issue and flot wasn't handling this reuse correctly.
        // 
        $("div.status_icon").remove()
    }
    pane.empty();
    setup_description(pane, rtn.start.substr(0, 10) + ' ----> ' + rtn.end.substr(0, 10));
    var this_div = $('<div this_rhic_table>');

    
    var Report = Backbone.Model.extend({});


    var PageableReports = Backbone.PageableCollection.extend({
        model : Report,
        state : {
            pageSize : 10
        },
        mode : "client"

    });

    var systems = rtn.list;
    systems.forEach(function(system){
        console.log(system);
        system.id = system.null;
        delete system.null;
    });

    var pageable_reports = new PageableReports(systems);

    var columns = [{
        name : "systemid",
        label : "System ID:",
        editable : false,
        cell : "string"
    },{
        name : "splice_server",
        label : "Satellite Server:",
        editable : false,
        cell : "string"
    }, {
        name : "organization",
        label : "Organization:",
        editable : false,
        cell : "string"
    }, {
        name : "updated",
        label : "Last Checkin:",
        editable : false,
        cell : "datetime"
    }, {
        name : "status",
        label : "Subscription Status:",
        editable : false,
        cell : "string"
    }];

    var ClickableRow = Backgrid.Row.extend({
        events : {
            "click" : "onClick"
        },
        onClick : function() {
            Backbone.trigger("rowclicked", this.model);
        }
    });

    Backbone.on("rowclicked", function(model) {
        console.log('in row click');
        createInstanceDetail(model);

    });

    // w/ paging
    var pageableGrid = new Backgrid.Grid({
        columns : columns,
        collection : pageable_reports,
        footer : Backgrid.Extension.Paginator,
        row : ClickableRow

    });

    var dash = $('<div class="dash">');
    var dashhead = $('<div class="dashhead">');
    var clearportal = $('<div class="fl clear portal">');
    var dashboard_subscriptions = $('<div id="dashboard_subscriptions">');


    dashboard_subscriptions.append('<hr width="350px">');
    var table = $('<table width=\"60%\"></table>');
    table.append('<tr><td><span><div class="small_status_icon small_status_icon_red"/>&nbsp Invalid Subscriptions</td><td></span>' + rtn.num_invalid + '</td></tr>'); // Red
    table.append('<tr><td><span><div class="small_status_icon small_status_icon_yellow"/>&nbsp Insufficient Subscriptions</td><td></span>' + rtn.num_partial + '</td></tr>'); // Yellow 
    table.append('<tr><td><span><div class="small_status_icon small_status_icon_green" />&nbsp Current Subscriptions</td><td></span>' + rtn.num_valid + '</td></tr>'); // Green
    table.append('<tr><td>&nbsp&nbsp&nbsp&nbsp&nbsp Inactive Systems</td><td>' + 0 + '</td></tr>'); //Orange

    table.append('</table>');
    dashboard_subscriptions.append(table);
    dashhead.append('<h2 class="fl">Subscription Status</h2>');
    dashhead.append('<div class="status_icon" alt="fail">');
    dashhead.append(dashboard_subscriptions);
    dash.append(dashhead);

    //RENDER DASHBOARD
    pane.append(dash);

    //CREATE FILTER
    var clientSideFilter = new Backgrid.Extension.ClientSideFilter({
        collection: pageable_reports,
        placeholder: "Search for systems",
        fields: {
          status: 5
        },
        
        ref: "id",
        wait: 150
    });

    //RENDER THE FILTER AND TABLE
    pane.append(clientSideFilter.render().$el);
    pane.append(pageableGrid.render().$el);
     
    var status_color = null;
    if (rtn.num_invalid > 0) {
        status_color = color_red;
    } else if (rtn.num_partial > 0) {
        status_color = color_yellow;
    } else if (rtn.num_valid > 0) {
        status_color = color_green;
    }
    // TODO: add "inactive" with color orange
    drawCircle("div.status_icon", status_color, ".80"); 

    return rtn.list.length
    

}


    

function createInstanceDetail(model) {
    console.log('in createInstanceDetail')
    date = model.get("date")
    instance = model.get("instance_identifier")
    var data = {
        "date": date,
        "instance": instance,
    };
    console.log(data);
    var InstanceDetail = Backbone.Model.extend({
        url : '/report-server/space/instance_details/'
    });

    var instanceDetails = new InstanceDetail();

    instanceDetails.save(data, {
        success : function(model, response) {
            console.log('SUCCESS');
            console.log(response);

            populateInstanceDetailReport(model);
            openDetail(); // this shouldn't be needed, but no harm in calling it again
            $('#detail_button').on("click", openDetail);
        }
    });
    
}

function populateInstanceDetailReport(rtn) {
    console.log('in pop instc details');
    var pane = $('#instance_details');
    var subscription_pane = $('<div id=subscription_pane>');
    pane.empty();
    //setup_description(pane, rtn.get('date'));
    if ($("div.system_status_icon").length) {
        // Attempting to work around 'flot' issue of:
        // Uncaught TypeError: Cannot call method 'shutdown' of undefined
        // Issue is that flot will attempt to 'reuse' the existing DOM element if it exists
        // We ran into an issue and flot wasn't handling this reuse correctly.
        //
        // Note:    This issue appeared with div.status_icon
        //          We are also applying work around for div.system_status_icon, just in case 
        $("div.system_status_icon").remove()
    }


    var facts = rtn.get('facts');
    var product_info = rtn.get('product_info')
    var status = rtn.get('status')
    var splice_server = rtn.get('splice_server')
    var system_id = rtn.get('system_id')
    var instance_identifier = rtn.get('instance_identifier')
    var date = rtn.get('date')
    var spacewalk = rtn.get('space_hostname')
    
    var ProductModel = Backbone.Model.extend();

    var ProductCollection = Backbone.Collection.extend({
        model : ProductModel
    });
    

    
    /*
     * curl -k -u admin:admin https://localhost:8443/candlepin/owners/admin/pools?consumer=e69871bb-170c-426a-844d-18f26632ffa4
     */
    
    
    var columnsInstance = [{
        name : "product_name",
        label : "Subscription:",
        cell : "string",
        editable: false
    },{
        name : "product_id",
        label : "Subscription ID:",
        cell : "string",
        editable: false
    },{
        name : "product_account",
        label : "Account:",
        cell : "string",
        editable: false
    },{
        name : "product_contract",
        label : "Contract:",
        cell : "string",
        editable: false
    },{
        name : "pool_sla",
        label : "SLA:",
        cell : "string",
        editable: false
    },{
        name : "pool_support",
        label : "Support:",
        cell : "string",
        editable: false
    },{
        name : "product_quantity",
        label : "Consumed:",
        cell : "string",
        editable: false
    },{
        name : "pool_start",
        label : "Start:",
        cell : "string",
        editable: false
    },{
        name : "pool_end",
        label : "End:",
        cell : "string",
        editable: false
    }];

    var ClickableRow = Backgrid.Row.extend({
        events : {
            "click" : "onClick"
        },
        onClick : function() {
            Backbone.trigger("subRowClicked", this.model);
        }
    });

    Backbone.on("subRowClicked", function(model) {
        console.log('in sub row click');
        subscriptionDetail(model, subscription_pane);
        subscription_pane.toggle("slow");
    });


    var columnsPool = [];
    
    var myinstance = new ProductCollection(product_info);

    var gridInstance = new Backgrid.Grid({
        columns : columnsInstance,
        collection : myinstance,
        row : ClickableRow
    });

    /*
    var gridPool = new Backgrid.Grid({
        columns : columnsPool,
        collection : myinstance
    });
*/

    var dash = $('<div class="dash">');
    var dashhead = $('<div class="dashhead">');
    var clearportal = $('<div class="fl clear portal">');
    var dashboard_subscriptions = $('<div id="dashboard_subscriptions">');


    dashboard_subscriptions.append('<hr width="350px">');
    var table = $('<table width=\"60%\"></table>');
    table.append('<tr><td>System ID: </td><td>' + system_id + '</td></tr>');
    table.append('<tr><td>Hostname: </td><td>' + 'sample_system.redhat.com' + '</td></tr>');
    var link_to_system = "<a href=https://" + spacewalk + "/rhn/systems/details/Overview.do?sid="+ system_id + ">Go to System Detail's Page </a>"
    table.append('<tr><td>Remediate: </td><td>' + link_to_system + '</td></tr>');
    table.append('<tr><td>Status: </td><td>' + 'Subscription SYS0395 is expired' + '</td></tr>');

    table.append('</table>');
    dashboard_subscriptions.append(table);
    dashhead.append('<h2 class="fl">System Subscription Status</h2>');
    dashhead.append('<div class="status_icon system_status_icon" alt="fail">');
    dashhead.append(dashboard_subscriptions);
    dash.append(dashhead);

    pane.append(dash);

    var status_color = null;
    switch (status) {
        case "partial":
            status_color = color_yellow;
            break;
        case "invalid":
            status_color = color_red;
            break;
        case "valid":
            status_color = color_green;
            break;
    }
    drawCircle("div.system_status_icon", status_color, ".80"); 


    pane.append('<br><br>');
    pane.append('<b>Subscriptions:</b>');
    pane.append(gridInstance.render().$el);
    pane.append('<br>');

    //SUBSCRIPTION DETAIL
    pane.append('<b>Subscription Detail</b>');
    button_details(pane, "subscription_detail_button", "  show/hide");
    subscription_pane.hide();
    $("#subscription_detail_button").click(function (){
            subscription_pane.toggle("slow");
            
    })

    pane.append(subscription_pane);


    //SYSTEM DETAIL
    pane.append('<b>System Details:</b>');
    var sys_detail_view = $('<div id=sys_detail>');
    button_details(pane, "sys_detail_button", "  show/hide");
    sys_detail_view.append("<li>&nbsp&nbsp Last Checkin: " + date + "</li>");
    sys_detail_view.append("<li>&nbsp&nbsp Satellite Server: " + spacewalk + "</li>");
    sys_detail_view.append("<li>&nbsp&nbsp Satellite Version: 5.6 </li>");
    sys_detail_view.append("<li>&nbsp&nbsp Organization Name: Marketing</li>");
    sys_detail_view.append("<li>&nbsp&nbsp Organization ID: 04</li>");
    sys_detail_view.append('<br></div>');
    sys_detail_view.hide();
    pane.append(sys_detail_view);
    $("#sys_detail_button").click(function (){
            sys_detail_view.toggle("slow");
            
    })

   
    
    //SYSTEM FACTS
    pane.append('<b>System Facts:</b>');
    var facts_view = $('<div id=instance_facts>');
    button_details(pane, "facts_button", "  show/hide");
    
    $.each(facts, function( key, value ){
        facts_view.append("<li>&nbsp&nbsp" + key + ": " + value + "</li>")
    });
    facts_view.append('<br></div>');
    facts_view.hide();
    pane.append(facts_view);
    $("#facts_button").click(function (){
            facts_view.toggle("slow");
            
    })


     //PROVIDED PRODUCTS
    pane.append('<b>Provided Products:</b>');
    var eng_prod_view = $('<div id=eng_prod>');
    button_details(pane, "eng_prod_button", "  show/hide");


    $.each(product_info, function(key, value){
        eng_prod_view.append("<b><li>&nbsp&nbsp" + value.product_name + "</li></b>")
        $.each(value.pool_provided_products, function( key, value ){
            eng_prod_view.append("<li>&nbsp&nbsp&nbsp&nbsp" + value.name  + "</li>")
        });
    });
    eng_prod_view.append('<br></div>');
    eng_prod_view.hide();
    pane.append(eng_prod_view);
    $("#eng_prod_button").click(function (){
            eng_prod_view.toggle("slow");
    })

     //INSTALLED PRODUCTS
    pane.append('<b>Installed Products:</b>');
    var install_eng_prod_view = $('<div id=install_eng_prod>');
    button_details(pane, "install_eng_prod_button", "  show/hide");
    install_eng_prod_view.append("<li>&nbsp&nbsp Red Hat Enterprise Linux Server</li>");

    install_eng_prod_view.append('<br></div>');
    install_eng_prod_view.hide();
    pane.append(install_eng_prod_view);
    $("#install_eng_prod_button").click(function (){
            install_eng_prod_view.toggle("slow");
    })

    if (!$('#instance_details').is(':visible')) {
        $('#instance_details').show();
    }


}





function subscriptionDetail(model, pane) {
    
    
    var product_id = model.get("product_id");

    var Subscription = Backbone.Model.extend({
        url: '/report-server/space/subscription/'
    });

    var data = {
        product_id: product_id
    };

    console.log(data);
    var subscription = new Subscription();

    subscription.save(data, {
        success: function(model, response){
            console.log('SUCCESS');
            console.log(response);
            //pane.append(JSON.stringify(response));
            //var pool_detail = JSON.parse(response);
            pane.empty();
            pane.append("&nbsp&nbsp<b>Subscription Name: </b>" + response.pool_detail.product_name + "<br><br>");
            pane.append("&nbsp&nbsp<b>Subscriptio ID: </b>" + response.pool_detail.product_id + "<br><br>");

            pane.append("&nbsp&nbsp<b>Provided Products: </b><br><br>");
            var provided_products = JSON.parse(response.provided_products);
            $.each(provided_products, function( key, value ){
                pane.append("<li>&nbsp&nbsp&nbsp&nbsp" + value.name  + "</li>")
            });

            pane.append("<br>&nbsp&nbsp<b>Product Attributes: </b><br><br>");
            var product_attributes = JSON.parse(response.product_attributes);
            $.each(product_attributes, function( key, value ){
                pane.append("<li>&nbsp&nbsp&nbsp&nbsp " + key + ": " + value +  "</li>");
            });

            pane.append('<br></div>');            

        }
    })

    
   
}

function createFactComplianceReport() {
  
}

function importData() {

}

function change_rhic_form(data){
    
}


    
function loadContent() {
   
}


function populateQuarantineReport(rtn) {
    
}

function populateFactComplianceReport(rtn, pane) {
  
}








