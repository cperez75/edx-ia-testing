!function(e){var t={};function n(r){if(t[r])return t[r].exports;var i=t[r]={i:r,l:!1,exports:{}};return e[r].call(i.exports,i,i.exports,n),i.l=!0,i.exports}n.m=e,n.c=t,n.d=function(e,t,r){n.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:r})},n.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},n.t=function(e,t){if(1&t&&(e=n(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var r=Object.create(null);if(n.r(r),Object.defineProperty(r,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var i in e)n.d(r,i,function(t){return e[t]}.bind(null,i));return r},n.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return n.d(t,"a",t),t},n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},n.p="/",n(n.s=204)}({204:function(e,t){function n(e){return(n="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}function r(e,t){for(var n=0;n<t.length;n++){var r=t[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(e,i(r.key),r)}}function i(e){var t=function(e,t){if("object"!==n(e)||null===e)return e;var r=e[Symbol.toPrimitive];if(void 0!==r){var i=r.call(e,t||"default");if("object"!==n(i))return i;throw new TypeError("@@toPrimitive must return a primitive value.")}return("string"===t?String:Number)(e)}(e,"string");return"symbol"===n(t)?t:String(t)}(function(e){var t=[],n=void 0!==window.LmsRuntime,o="/static/studio/js/vendor/tinymce/js/tinymce/";n&&(o="/static/js/vendor/tinymce/js/tinymce/"),void 0===window.tinymce&&(t.push("tinymce"),t.push("jquery.tinymce")),e(t,(function(){var e=function(){function e(){var t,n,r;!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,e),t=this,r=[],(n=i(n="editorInstances"))in t?Object.defineProperty(t,n,{value:r,enumerable:!0,configurable:!0,writable:!0}):t[n]=r}var t,n,u;return t=e,(n=[{key:"getTinyMCEConfig",value:function(e){var t={menubar:!1,statusbar:!1,base_url:o,theme:"silver",skin:"studio-tmce5",content_css:"studio-tmce5",height:"300",schema:"html5",plugins:"code image link lists",toolbar:"formatselect | bold italic underline | link blockquote image | numlist bullist outdent indent | strikethrough | code | undo redo"};return e&&(t=Object.assign(t,{toolbar:!1,readonly:1})),t}},{key:"load",value:function(e){this.elements=e;var t=this;return Promise.all(this.elements.map((function(){var e=this,n=$(this).attr("disabled"),r=$(this).attr("id");if(void 0!==r){var i=tinymce.get(r);i&&i.destroy()}var o=t.getTinyMCEConfig(n);return new Promise((function(n){o.setup=function(e){return e.on("init",(function(){t.editorInstances.push(e),n()}))},$(e).tinymce(o)}))})))}},{key:"setOnChangeListener",value:function(e){var t=this;["change","keyup","drop","paste"].forEach((function(n){t.editorInstances.forEach((function(t){t.on(n,e)}))}))}},{key:"response",value:function(e){if(void 0===e)return this.editorInstances.map((function(e){return e.getContent()}));this.editorInstances.forEach((function(t,n){t.setContent(e[n])}))}}])&&r(t.prototype,n),u&&r(t,u),Object.defineProperty(t,"prototype",{writable:!1}),e}();return function(){return new e}}))}).call(window,window.define||window.RequireJS.define)}});
//# sourceMappingURL=ieia-editor-tinymce.0b97b77ad7f1b7150f67.js.map