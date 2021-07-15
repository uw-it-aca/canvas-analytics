'use strict'
const path = require("path")
const webpack = require('webpack')
const BundleTracker = require('webpack-bundle-tracker')
const VueLoaderPlugin = require('vue-loader/lib/plugin')
const CleanWebpackPlugin = require('clean-webpack-plugin')

module.exports = {
    mode: 'development',
    context: __dirname,
    entry: {
        admin_jobs: './data_aggregator/static/vue/admin/jobs.js',
        admin_job_detail: './data_aggregator/static/vue/admin/job_detail.js',
        api_analytics: './data_aggregator/static/vue/api/analytics.js',
    },
    output: {
        path: path.resolve('./data_aggregator/static/data_aggregator/bundles/'),
        filename: "[name]-[hash].js",
    },
    plugins: [
        new CleanWebpackPlugin(),
        new BundleTracker({
            filename: './data_aggregator/static/webpack-stats.json'
        }),
        new VueLoaderPlugin(),
    ],
    module: {
        rules: [{
                test: /\.vue$/,
                loader: 'vue-loader'
            },
            {
                test: /\.s[ac]ss$/,
                sideEffects: true,
                use: [
                    // Creates `style` nodes from JS strings
                    "style-loader",
                    // Translates CSS into CommonJS
                    "css-loader",
                    // Compiles Sass to CSS
                    "sass-loader",
                  ],
            },
            {
                test: /\.css$/,
                sideEffects: true,
                use: [
                    // Creates `style` nodes from JS strings
                    "style-loader",
                    // Translates CSS into CommonJS
                    "css-loader",
                  ],
            },
            {
                test: /\.(png|svg|jpg|gif|woff|woff2|eot|ttf|svg)$/,
                use: ['file-loader']
            },
        ]
    },
    resolve: {
        extensions: ['.js', '.vue'],
        alias: {
            'vue$': 'vue/dist/vue.esm.js'
        }
    }
}

if (process.env.BUNDLE_ANALYZER === "True") {
    module.exports.plugins.push(
      new BundleAnalyzerPlugin({
        analyzerHost: '0.0.0.0',
      })
    );
  }
