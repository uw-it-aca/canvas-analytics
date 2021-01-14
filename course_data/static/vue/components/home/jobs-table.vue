<template>
  <div class="overflow-auto">
    <b-pagination
      v-model="currentPage"
      :total-rows="totalRows"
      :per-page="perPage"
      aria-controls="jobs-table"
      size="sm"
      limit="10"
      first-number
      last-number
      >
    </b-pagination>
    <b-table id="jobs-table"
      :items="jobs"
      :fields="fields"
      :per-page="perPage"
      :busy="isLoading"
      :current-page="currentPage"
      fixed
      bordered
      small
      >

      <template slot="top-row" slot-scope="{ fields }">
        <td v-for="field in fields" :key="field.key">
          <b-form v-if="field.key == 'message'" class="d-flex flex-nowrap" inline>
            <b-form-select v-model="selected_restart_option" id="restart-select" name="restart-select" class="small-select">
              <b-form-select-option :value="'all'">restart all</b-form-select-option>
              <b-form-select-option :value="'failed'">restart failed</b-form-select-option>
              <b-form-select-option :value="'completed'">restart completed</b-form-select-option>
            </b-form-select>
            <b-button v-show="field.key=='message'" size="sm" class="mr-2 pill-button">
              <b-icon icon="arrow-clockwise"></b-icon>
            </b-button>
          </b-form>
        </td>
      </template>

      <template #table-colgroup="scope">
        <col
          v-for="field in scope.fields"
          :key="field.key"
          :style="{ width: field.key === 'message' ? '125%' : '100%' }"
        >
      </template>

      <template #table-busy>
        <div class="text-center text-danger my-2">
          <b-spinner class="align-middle"></b-spinner>
          <strong>Loading...</strong>
        </div>
      </template>

      <template #cell(context)="row">
        <ul class="list-unstyled m-0">
          <li v-for="(value, name) in row.item.context" :key="value">
            {{name}} : {{ value }}
          </li>
        </ul>
      </template>

      <template #cell(start)="row">
        {{row.item.start | date}}
      </template>

      <template #cell(end)="row">
        {{row.item.end | date}}
      </template>
  
      <template #cell(message)="row">
        {{getStatus(row.item)}}
        <b-button v-show="getStatus(row.item) == 'failed' || getStatus(row.item) == 'completed'" size="sm" @click="restartJobs([row.item.id])" class="mr-2 pill-button ">
          <b-icon icon="arrow-clockwise"></b-icon>
        </b-button>
      </template>
    </b-table>
  </div>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import dataMixin from '../../mixins/data_mixin';
import utilitiesMixin from '../../mixins/utilities_mixin';

export default {
  name: 'jobs-table',
  mixins: [dataMixin, utilitiesMixin],
  props: ['jobs'],
  data: function() {
    return {
      fields: [
        { key: 'job_type',
          label: 'Job Type',
          sortable: true,
        },
        { key: 'context',
          label: 'Job Context',
          sortable: true,
        },
        { key: 'message',
          label: 'Job Status',
          tdClass: (value, key, item) => {
              return 'table-' + this.getStatus(item);
          },
        },
        { key: 'start',
          label: 'Job Start',
          sortable: true,
        },
        { key: 'end',
          label: 'Job End',
          sortable: true,
        },
      ],
      selected_restart_option: 'all',
      perPage: 500,
      currentPage: 1,
    }
  },
  computed: {
    ...mapState({
      isLoading: (state) => state.isLoading,
      totalRows() {
        return this.jobs.length
      }
    }),
  },
  methods: {
    ...mapMutations([
      'addVarToState',
    ]),
  },
};
</script>

<style>
  .table-pending {
    color: #818182;
    background-color: #fefefe;
    border-color: #fdfdfe;
  }

  .table-running {
    color: #0c5460;
    background-color: #d1ecf1;
    border-color: #bee5eb;
  }

  .table-completed {
    color: #155724;
    background-color: #d4edda;
    border-color: #c3e6cb;
  }

  .table-failed {
    color: #721c24;
    background-color: #f8d7da;
    border-color: #f5c6cb;
  }

  .small-select {
    height: 25px;
    padding: 0px 5px;
    width: 100% !important;
  }

  .pill-button {
    background-color: #ddd;
    border-style: solid;
    border-width: 1px;
    border-radius: 4px;
    border-color: darkgray;
    color: black;
    padding: 3px 5px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    margin: 2px 1px;
    cursor: pointer;
    font-size: 10px;
  }
</style>

