import Vue from 'vue';
import Vuex from 'vuex';

import { BootstrapVue, BootstrapVueIcons } from 'bootstrap-vue'

// Import Bootstrap an BootstrapVue CSS files (order is important)
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

// Make BootstrapVue available throughout project
Vue.use(BootstrapVue);
Vue.use(BootstrapVueIcons);

// vuex
Vue.use(Vuex);

Vue.config.devtools = true;

export {Vue};
