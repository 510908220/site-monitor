/**
 * Created by Administrator on 2016/5/31 0031.
 */
String.prototype.format = function (args) {
    var result = this;
    if (arguments.length > 0) {
        if (arguments.length == 1 && typeof (args) == "object") {
            for (var key in args) {
                if (args[key] != undefined) {
                    var reg = new RegExp("({" + key + "})", "g");
                    result = result.replace(reg, args[key]);
                }
            }
        }
        else {
            for (var i = 0; i < arguments.length; i++) {
                if (arguments[i] != undefined) {
                    var reg = new RegExp("({[" + i + "]})", "g");
                    result = result.replace(reg, arguments[i]);
                }
            }
        }
    }
    return result;
}

var api_tool = (function () {
    // your module code goes here
    var API_MONITOR_GROUP = "/api/mgroups/"
    var API_CONTACT_URL = "/api/contacts/";
    var API_CONTACT_GROUP_URL = "/api/cgroups/";
    return {
        get_monitor_group_by_name: function (name) {
            var monitor_group;
            $.ajax({
                url: API_MONITOR_GROUP + name + "/",
                type: 'GET',
                async: false,
                dataType: 'json',

                success: function (data) {
                    monitor_group = data;
                },
                error: function (xhr, textStatus) {
                    console.log(xhr)
                    console.log(textStatus)
                }
            })
            return monitor_group;
        },
        get_contacts: function () {
            var contacts;
            $.ajax({
                url: API_CONTACT_URL,
                type: 'GET',
                async: false,
                dataType: 'json',

                success: function (data) {
                    contacts = data;
                },
                error: function (xhr, textStatus) {
                    console.log(xhr)
                    console.log(textStatus)
                }
            })
            return contacts;
        },
        get_contact_groups: function () {
            var contact_groups;
            $.ajax({
                url: API_CONTACT_GROUP_URL,
                type: 'GET',
                async: false,
                dataType: 'json',

                success: function (data) {
                    contact_groups = data;
                },
                error: function (xhr, textStatus) {
                    console.log(xhr)
                    console.log(textStatus)
                }
            })
            return contact_groups;
        },
        get_monitor_groups: function () {
            var monitor_groups = {};
            $.ajax({
                url: API_MONITOR_GROUP,
                type: 'GET',
                async: false,
                dataType: 'json',

                success: function (data) {
                    for (var item of data) {
                        monitor_groups[item.id] = item;
                    }
                },
                error: function (xhr, textStatus) {
                    console.log(xhr)
                }
            })
            return monitor_groups;
        },
        is_json: function (str) {
            try {
                JSON.parse(str);
            } catch (e) {
                return false;
            }
            return true;
        }

    }
}());

var number_tool = (function () {
    return {
        format_time: function (sec) {
            if (sec < 60) {
                return sec + " 秒";

            }
            else if (sec >= 60 && sec < 3600) {
                return parseInt(sec / 60) + " 分钟";
            }
            else if (sec >= 3600 && sec < 86400) {
                return parseInt(sec / 3600) + " 小时";
            }
            else if (sec >= 86400) {
                return parseInt(sec / 86400) + " 天";
            }
        },
        format_size: function (bytes) {
            var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            if (bytes == 0) return 'n/a';
            var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
            if (i == 0) return bytes + ' ' + sizes[i];
            return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
        }

    }
}());