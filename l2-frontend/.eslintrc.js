module.exports = {
  root: true,
  env: {
    node: true,
  },
  extends: [
    'plugin:vue/essential',
    '@vue/airbnb',
    '@vue/typescript/recommended',
  ],
  parserOptions: {
    ecmaVersion: 2020,
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    '@typescript-eslint/ban-ts-comment': 'off',
    'no-plusplus': 'off',
    "no-restricted-syntax": ["error", "ForInStatement", "LabeledStatement", "WithStatement"],
    'no-continue': 'off',
    'no-await-in-loop': 'off',
    'max-len': ["error", { "code": 130 }],
    'camelcase': 'off',
    'arrow-parens': 'off',
    "@typescript-eslint/explicit-module-boundary-types": "off",
    "@typescript-eslint/no-explicit-any": "off",
    'func-names': 'off',
    "@typescript-eslint/prefer-optional-chain": "error",
  },
  "overrides": [
    {
      "files": ["*.ts", "*.tsx"],
      "rules": {
        "@typescript-eslint/explicit-module-boundary-types": ["off"],
      }
    }
  ],
};
