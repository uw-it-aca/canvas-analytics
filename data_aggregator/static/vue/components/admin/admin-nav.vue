<template>
<div>
  <b-navbar toggleable="sm" class="nav-menu">
    <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>
    <b-collapse id="nav-collapse" is-nav>
      <b-navbar-nav>
        <b-nav-item href="/admin/jobs/">Automated Jobs</b-nav-item>
        <b-nav-item href="/admin/metadata/">Metadata Files</b-nav-item>
      </b-navbar-nav>
    </b-collapse>
  </b-navbar>
</div>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import utilitiesMixin from '../../mixins/utilities_mixin';

export default {
  name: 'admin-nav',
  mixins: [utilitiesMixin],
  computed: {
    ...mapState({
    }),
  },
  created: function() {
  },
  methods: {
    
    ...mapMutations([
    ]),
  },
};
</script>

<style>
</style>
