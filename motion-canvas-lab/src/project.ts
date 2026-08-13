import {makeProject} from '@motion-canvas/core';

import testingPapers from './scenes/testing-papers?scene';
import viewer from './scenes/viewer?scene';

export default makeProject({
  scenes: [viewer, testingPapers],
});
