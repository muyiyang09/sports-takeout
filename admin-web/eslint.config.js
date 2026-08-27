import pluginVue from 'eslint-plugin-vue';
import vueTsEslintConfig from '@vue/eslint-config-typescript';

// ESLint flat config（§5.23）：vue + ts 推荐规则
export default [
    { ignores: ['dist/**', 'node_modules/**'] },
    ...pluginVue.configs['flat/recommended'],
    ...vueTsEslintConfig(),
    {
        rules: {
            'vue/multi-word-component-names': 'off'
        }
    }
];
