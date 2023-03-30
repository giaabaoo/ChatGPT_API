python opt_chatgpt_dial_gen.py \
--api_key your_openapi_key \
--syn_dials synCP_dials.json \
--num_samples 400 
python process_chatgpt_results.py
python gen_annotations.py