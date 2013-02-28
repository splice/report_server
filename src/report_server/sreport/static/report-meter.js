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
    setupCreateForm();
    setupCreateDatesForm();
    openCreate();
    navButtonDocReady();
    
    
    

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


function setupCreateForm(){
    var select_contract = $('#contract');
    var select_rhic = $('#rhic');
    var select_env = $('#env');
    
    select_contract.empty();
    select_rhic.empty();
    select_env.empty();
    
    var FormDatum = Backbone.Model.extend({});

    var FormData = Backbone.Collection.extend({
      model: FormDatum,
      url: '/report-server/meter/report_form/'
    });
    
    var AppView = Backbone.View.extend({
      
      initialize: function() {
        _.bindAll(this, 'render');
        this.collection.bind('reset', this.render);
        this.collection.fetch();
      },
      
      render: function(){

        this.collection.each(function(item) {
            var list = item.get('contracts')
            
            select_contract.append($('<option selected value=All>All</option>'));
            for (i in list){
                select_contract.append($('<option value=' + list[i] + '>' + list[i] + '</option>'));
            }
            
            select_rhic.append($('<option selected value=All>All</option>'));
            var list = item.get('list_of_rhics')
            for (i in list){
               select_rhic.append($('<option value=' + list[i][0] + '>' + list[i][1] + '</option>'));
            }
            var list = item.get('environments')
            for (i in list){
               select_env.append($('<option value=' + list[i] + '>' + list[i] + '</option>'));
            }
         
        });
        
        select_contract.chosen();
        select_rhic.chosen();
        select_env.chosen();
      }
      
    });
    
    var appview = new AppView({ collection: new FormData() });

}

function setupCreateDatesForm(){
    date_2 = Date.today();
    date_1 = (1).months().ago();
    date_0 = (2).months().ago();
    
    $('#byMonth').append($('<option  value=' + '-1' + ' ></option>'));
    
    [date_0, date_1, date_2].forEach(function(item){
        $('#byMonth').append($('<option selected value=' + item.toString("M") + ',' + item.toString("yyyy") +  '>' + item.toString("MMM") + ' ' + item.toString("yyyy") + '</option>'));
    });

    $('#startDate').datepicker();
    $('#endDate').datepicker();
    $('#byMonth').chosen();
}


function updateListOfRHICS() {

}



function createReport(event) {
    event.preventDefault();
    form_filter_link_hide(false);
    if (logged_in){
        var CreateReport = Backbone.Model.extend({
            url: '/report-server/meter/report/'
        });
        
        var data = {
            byMonth:            $('#byMonth').val(),
            startDat:           $('#startDate').val(),
            endDate:            $('#endDate').val(),
            contract_number:    $('#contract').val(),
            rhic:               $('#rhic').val()
        };
        
        var createReport = new CreateReport();
        console.log(createReport.toJSON());
        
        createReport.save( data, {
            success: function(model, response){
                console.log('SUCCESS');
                console.log(response);
                
                $('#report_pane > div').empty();
                var pane = '#report_pane > div';
                //populateReportBB(response, pane );
                populateReportBG(response, pane );
                openReport();
            }
        });
        
        }
        
	
}

function populateReportBG(rtn, pane) {
    var pane = $('#report_pane > div');
    var this_div = $('<div this_rhic_table>');
    pane.append('<h3>Date Range: ' + rtn.start.substr(0, 10) + ' ----> ' + rtn.end.substr(0, 10) + '</h3>');
    pane.append('<br><br>');
    var show_details = $('<button id=show_details style="float: right" class="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only" >Show Details</button>');
    var Report = {};
    

    
    var Report = Backbone.Model.extend();
    
    var Reports = Backbone.Collection.extend({
        model: Report
        
    });
    
    var PageableReports = Backbone.PageableCollection.extend({
        model: Report,
        state: {
            pageSize: 3
        },
        mode: "client"
        
    });
        
    var mylist = []
    for (i = 0; i < rtn.list.length; i++){
        for (j = 0; j < rtn.list[i].length; j++){
            var row = rtn.list[i][j];
            row.description = [row.product_name, row.sla, row.support, row.facts];
            row.action = [row.start, row.end, row.description, row.filter_args_dict];
            mylist.push(row);
            
        }
    }
    var reports = new Reports(mylist);
    var pageable_reports = new PageableReports(mylist);
            
    var columns = [{
      name: "rhic", 
      label: "RHIC:", 
      editable: false,
      cell: "string"
    }, {
      name: "product_name",
      label: "Product:",
      editable: false,
      cell: "string"
    }, {
      name: "sla",
      label: "SLA:",
      editable: false,
      cell: "string"
    }, {
      name: "support",
      label: "Support:",
      editable: false,
      cell: "string"
    }, {
      name: "contract_use",
      label: "Contract Use:",
      editable: false,
      cell: "string"
    }, {
      name: "nau",
      label: "Usage:",
      editable: false,
      cell: "string"
    }, {
      name: "compliant",
      label: "Compliant:",
      editable: false,
      cell: "string"
      }];
    
    
    var ClickableRow = Backgrid.Row.extend({
        events: {
        "click": "onClick"
    },
    onClick: function () {
        Backbone.trigger("rowclicked", this.model);
       }
    });

    Backbone.on("rowclicked", function (model) {
        console.log('in row click');

        var description = {};
        description["Product"] = model.get('product_name');
        description["SLA"] = model.get('sla');
        description["Support"] = model.get('support');
        description["Facts"] = model.get('facts');
        var filter_args = JSON.parse(model.get('filter_args_dict'));
        createMax(model.get('start'), model.get('end'), description, filter_args);
    });


    // w/ paging
    var pageableGrid = new Backgrid.Grid({
        columns: columns,
        collection: pageable_reports,
        footer: Backgrid.Extension.Paginator,
        row: ClickableRow
        
    });
    
    pane.append(pageableGrid.render().$el);
    

return rtn.list.length


}

    

function createMax(start, end, description, filter_args) {
    closeDetail();
    closeMax();
    console.log('in max');
    console.log(start);
    console.log(end);
    console.log(description);
    console.log(filter_args);
    
        
    var MaxReport = Backbone.Model.extend({
        url : '/report-server/meter/max_report/'
    });

    var data = {
        "start": start,
        "end": end,
        "description": description,
        "filter_args_dict": filter_args
    };
    
    console.log(data);

    var maxReport = new MaxReport();

    maxReport.save(data, {
        success : function(model, response) {
            console.log('SUCCESS');
            console.log(response);

            $('#max_pane > div').empty();
            var pane = '#max_pane > div';
            
            openMax();
            $('#max_button').on("click", openMax);
            populateMaxReport(model);
        }
    }); 

}

function populateMaxReport(rtn) {
    var pane = $('#max_pane');
    pane.empty();
    
    var contract = rtn.get('daily_contract');
    var date = rtn.get('date');
    var description = rtn.get('description');
    var end = rtn.get('end');
    var filter_args = rtn.get('filter_args');
    var list = rtn.get('list');
    var mcu = rtn.get('mcu');
    var mdu = rtn.get('mdu');
    var start = rtn.get('start');
    
    var desc_start = new Date(0);
    var desc_end = new Date(0);
    desc_start.setUTCSeconds(start);
    desc_end.setUTCSeconds(end);
    
    //setup description
    pane.append('<h3>Date Range: ' + desc_start.toDateString().substr(0,10) + ' ----> ' + desc_end.toDateString().substr(0,10) + '</h3>');
    pane.append('<br><br>');
    var header = $('<b> ' +  setup_description(description) + '</b>' );
    pane.append(header);
    
    if (list.length > 0){
        pane.append($('<br></br>'));
        pane.append($('<div id="chartdiv" style="height:400px;width:100%; "></div>'));
        
        var plot1 = $.jqplot('chartdiv', [mdu, mcu, contract],
                {
                    title:'MDU vs MCU',
                    axesDefaults: {
                        labelRenderer: $.jqplot.CanvasAxisLabelRenderer
                    },
                    
                    axes: {
                        xaxis:{
                            label: "Date Range",
                            renderer:$.jqplot.DateAxisRenderer, 
                            tickRenderer: $.jqplot.CanvasAxisTickRenderer,
                            tickOptions: {
                              angle: -30,
                              formatString: '%b %e %Y'
                            } 
                        },
                        yaxis:{
                            label: "Number of Resources",
                            pad: 1.3
                        }
                    },
                    highlighter: {
                        show: true,
                        sizeAdjust: 10.5,
                        useAxesFormatters: true
                    },
                    cursor: {
                        show: true
                    },
                    legend: {
                        show: true,
                        location: 'se',
                        yoffset: 500
                        
                    },
                    series:[
                        {
                            label: 'MDU',
                            lineWidth:2,
                            markerOptions: { style:'dimaond' } 
                        },
                        {
                            label: 'MCU',
                            markerOptions: { sytle:'circle'}
                        },
                        {
                            label: 'Contracted Use',
                            lineWidth:5,
                            color: '#FF0000',
                            markerOptions: { style:"filledSquare", size:10 }
                        }
                    ]
                    
                });
        $('#chartdiv').bind('jqplotDataClick', function (ev, seriesIndex, pointIndex, data) { 
               //alert("test" + "," + data[0] + "," + data[1]);
               var this_date = new Date(data[0]);
               var date_to_send = (this_date.getMonth() + 1) + "-" + this_date.getDate() + "-" + this_date.getFullYear();
               createDetail( date_to_send, description,  escape(new String(filter_args)));
              });
    
        glossary_mdu(pane);
        
        
        //BEGIN LIST
        var show_details = $('<button id=show_details class="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only" >Show Details</button>');
        pane.append(show_details);
        pane.append('<br><br>');
        var list_view = $('<div id=list_view>');

        var Max = Backbone.Model.extend();
    
        var MaxList = Backbone.Collection.extend({
            model: Max
            
        });
        
        var PageableMaxList = Backbone.PageableCollection.extend({
            model: Max,
            state: {
                pageSize: 25
            },
            mode: "client"
            
        });
        
        
        
        var columns = [{
            name: "date",
            label: "Date",
            cell: "string"
        },{
            name: "mdu",
            label: "MDU",
            cell: "string"
        },{
            name: "mcu",
            label: "MCU",
            cell: "string"
        }];
        
        var ClickableMaxRow = Backgrid.Row.extend({
        events: {
            "click": "onClick"
        },
        onClick: function () {
            Backbone.trigger("maxrowclicked", this.model);
           }
        });
    
        Backbone.on("maxrowclicked", function (model) {
            console.log('in max row click');
        });
        
        var mylist = new PageableMaxList(list);
        // w/ paging
        var pageableGrid = new Backgrid.Grid({
            columns: columns,
            collection: mylist,
            footer: Backgrid.Extension.Paginator,
            row: ClickableMaxRow
        
        });


        
        list_view.append(pageableGrid.render().$el);
        list_view.hide();
        pane.append(list_view);
        
        
        $("button").click(function (){
            list_view.toggle("slow");
            
          })
          
    } else {
        pane.append($('<h3>This date range contains no usage data.</h3><br></br><br></br>'));
    }
}
        



function create_default_report(event){
   
}

function createDetail(date, description,  filter_args) {
   
}


function createInstanceDetail(date, instance, filter_args) {
    
}

function createQuarantineReport() {
   
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



function populateDetailReport(rtn) {
   
}

function populateInstanceDetailReport(rtn) {
 
}


