const { createConfig } = require('@edx/frontend-build');
const { mergeWithRules } = require('webpack-merge');
const presets = require('@edx/frontend-build/lib/presets')

const webpack = require('webpack');
const path = require('path');
const Dotenv = require('dotenv-webpack');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const PostCssAutoprefixerPlugin = require('autoprefixer');
const CssNano = require('cssnano');
const { WebpackManifestPlugin } = require('webpack-manifest-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

// Get base config from edx-platform
let config = createConfig('webpack-prod');

// Modify CSS processing rules (remove PostCssRtlPlugin)
const modifiedCssRule = {
  module: {
    rules: [
      // This babel-loader config is pulled from frontend-build@13.0.4
      // When we update frontend-build to above that version, this section
      // can be removed and we can fallback to the implementation upstream.
      //
      // We had to do this because frontend-build is currently too far behind
      // and can't easily be updated to a newer version without upgrading
      // webpack and many other libraries.
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules\/(?!@(open)?edx)/,
        use: {
          loader: 'babel-loader',
          options: {
            configFile: presets.babel.resolvedFilepath,
          },
        },
      },
      {
        test: /(.scss|.css)$/,
        use: [
          MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader', // translates CSS into CommonJS
            options: {
              sourceMap: true,
            },
          },
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: () => [
                  PostCssAutoprefixerPlugin({ grid: true }),
                  CssNano(),
                ],
              },
            },
          },
          'resolve-url-loader',
          {
            loader: 'sass-loader', // compiles Sass to CSS
            options: {
              sourceMap: true,
              sassOptions: {
                includePaths: [
                  path.join(process.cwd(), 'node_modules'),
                  path.join(process.cwd(), 'src'),
                ],
              },
            },
          },
        ],
      },
    ],
  },
};

// Merge back to configuration
config = mergeWithRules({
  module: {
    rules: {
      test: 'match',
      exclude: 'replace',
      use: 'replace',
    },
  },
})(config, modifiedCssRule);

Object.assign(config, {
  entry: {
    'ieia-lms': path.resolve(process.cwd(), 'ieia/xblock/static/js/src/lms_index.js'),
    'ieia-studio': path.resolve(process.cwd(), 'ieia/xblock/static/js/src/studio_index.js'),
    'ieia-rtl': path.resolve(process.cwd(), 'ieia/xblock/static/sass/ieia-rtl.scss'),
    'ieia-ltr': path.resolve(process.cwd(), 'ieia/xblock/static/sass/ieia-ltr.scss'),
    'ieia-editor-textarea': path.resolve(process.cwd(), 'ieia/xblock/static/js/src/lms/editors/oa_editor_textarea.js'),
    'ieia-editor-tinymce': path.resolve(process.cwd(), 'ieia/xblock/static/js/src/lms/editors/oa_editor_tinymce.js'),
  },
  optimization: {},
  plugins: [
    // Cleans the dist directory before each build
    new CleanWebpackPlugin(),
    new Dotenv({
      path: path.resolve(process.cwd(), '.env'),
      systemvars: true,
    }),
    new MiniCssExtractPlugin({
      filename: '[name].[chunkhash].css',
    }),
    new webpack.ProvidePlugin({
      Backgrid: path.resolve(path.join(__dirname, 'ieia/xblock/static/js/lib/backgrid/backgrid')),
    }),
    new WebpackManifestPlugin({
      seed: {
        base_url: '/static/dist',
      },
    }),
  ],
});

config.resolve.modules = ['node_modules', path.resolve(__dirname, 'ieia/xblock/static/js/src')];
config.output.path = path.resolve(process.cwd(), 'ieia/xblock/static/dist');

module.exports = config;
