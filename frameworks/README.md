# README

## SeeAct
1. Create a conda environment and install dependency:
```bash
python3 -m venv venv
 . venv/bin/activate
pip install seeact
```

## core
* get_interactive_elements_with_playwright
  * the goal is to generate SoM: set of marks
  * https://github.com/OSU-NLP-Group/SeeAct/blob/main/seeact_package/seeact/agent.py#L503-L504
* predict
  * https://github.com/OSU-NLP-Group/SeeAct/blob/main/seeact_package/seeact/agent.py#L582-L583
  * https://github.com/OSU-NLP-Group/SeeAct/blob/main/seeact_package/seeact/demo_utils/inference_engine.py#L230-L270
* take action
  * https://github.com/OSU-NLP-Group/SeeAct/blob/main/seeact_package/seeact/agent.py#L403

## TODO
* get_interactive_elements_with_playwright
  * need to be associated with axtree
  * def screenshots_som(self):
    * return self.get_screenshots(som=True)
* show on frontend
* take screenshot