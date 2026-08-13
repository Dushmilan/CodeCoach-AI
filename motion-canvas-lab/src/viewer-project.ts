import {makeProject} from '@motion-canvas/core';

import viewer from './scenes/viewer?scene';

// Project used by the chrome-less embedded viewer (viewer.html). It contains
// ONLY the data-driven viewer scene — never the testing-papers playground —
// so the app's animation modal plays the animation and nothing else.
export default makeProject({
  scenes: [viewer],
});
