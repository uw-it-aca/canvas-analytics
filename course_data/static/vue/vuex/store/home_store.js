import {fetchBuilder, extractData, buildWith} from './model_builder';

const customActions = {
    fetch: fetchBuilder('/', extractData, 'json'),
};

export default buildWith(
    {customActions},
);
