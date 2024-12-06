# # Customer support agent with Amazon Bedrock

# ## Preparation
import subprocess
import sys
subprocess.check_call([sys.executable, 'sh','./ro_shared_data/reset.sh'])

import os
import boto3
import uuid, json
import json
from helper import *

region_name = 'us-west-2'
roleArn = os.environ['BEDROCKAGENTROLE']
lambda_function_arn = os.environ['LAMBDA_FUNCTION_ARN']
knowledgeBaseId = os.environ['KNOWLEDGEBASEID']

bedrock_agent = boto3.client(service_name='bedrock-agent', region_name=region_name)
bedrock_agent_runtime = boto3.client(service_name='bedrock-agent-runtime', region_name=region_name)




################################################# #  Customer support agent with Amazon Bedrock # #################################################

create_agent_response = bedrock_agent.create_agent(
    agentName='mugs-customer-support-agent',
    foundationModel='anthropic.claude-3-haiku-20240307-v1:0',
    instruction="""You are an advanced AI agent acting as a front line customer support agent.""",
    agentResourceRoleArn=roleArn
)

agentId = create_agent_response['agent']['agentId']

wait_for_agent_status(
    agentId=agentId, 
    targetStatus='NOT_PREPARED'
)

bedrock_agent.prepare_agent(
    agentId=agentId
)

wait_for_agent_status(
    agentId=agentId, 
    targetStatus='PREPARED'
)

create_agent_alias_response = bedrock_agent.create_agent_alias(
    agentId=agentId,
    agentAliasName='MyAgentAlias',
)

agentAliasId = create_agent_alias_response['agentAlias']['agentAliasId']

wait_for_agent_alias_status(
    agentId=agentId,
    agentAliasId=agentAliasId,
    targetStatus='PREPARED'
)

############################################################ # Connecting with a CRM # ############################################################

create_agent_action_group_response = bedrock_agent.create_agent_action_group(
    actionGroupName='customer-support-actions',
    agentId=agentId,
    actionGroupExecutor={
        'lambda': lambda_function_arn
    },
    functionSchema={
        'functions': [
            {
                'name': 'customerId',
                'description': 'Get a customer ID given available details. At least one parameter must be sent to the function. This is private information and must not be given to the user.',
                'parameters': {
                    'email': {
                        'description': 'Email address',
                        'required': False,
                        'type': 'string'
                    },
                    'name': {
                        'description': 'Customer name',
                        'required': False,
                        'type': 'string'
                    },
                    'phone': {
                        'description': 'Phone number',
                        'required': False,
                        'type': 'string'
                    },
                }
            },            
            {
                'name': 'sendToSupport',
                'description': 'Send a message to the support team, used for service escalation. ',
                'parameters': {
                    'custId': {
                        'description': 'customer ID',
                        'required': True,
                        'type': 'string'
                    },
                    'supportSummary': {
                        'description': 'Summary of the support request',
                        'required': True,
                        'type': 'string'
                    }
                }
            }
        ]
    },
    agentVersion='DRAFT',
)

actionGroupId = create_agent_action_group_response['agentActionGroup']['actionGroupId']

wait_for_action_group_status(
    agentId=agentId, 
    actionGroupId=actionGroupId,
    targetStatus='ENABLED'
)

bedrock_agent.prepare_agent(
    agentId=agentId
)

wait_for_agent_status(
    agentId=agentId,
    targetStatus='PREPARED'
)

bedrock_agent.update_agent_alias(
    agentId=agentId,
    agentAliasId=agentAliasId,
    agentAliasName='MyAgentAlias',
)

wait_for_agent_alias_status(
    agentId=agentId,
    agentAliasId=agentAliasId,
    targetStatus='PREPARED'
)

########################################################### # Performing calculations # ###########################################################


update_agent_action_group_response = bedrock_agent.update_agent_action_group(
    actionGroupName='customer-support-actions',
    actionGroupState='ENABLED',
    actionGroupId=actionGroupId,
    agentId=agentId,
    agentVersion='DRAFT',
    actionGroupExecutor={
        'lambda': lambda_function_arn
    },
    functionSchema={
        'functions': [
            {
                'name': 'customerId',
                'description': 'Get a customer ID given available details. At least one parameter must be sent to the function. This is private information and must not be given to the user.',
                'parameters': {
                    'email': {
                        'description': 'Email address',
                        'required': False,
                        'type': 'string'
                    },
                    'name': {
                        'description': 'Customer name',
                        'required': False,
                        'type': 'string'
                    },
                    'phone': {
                        'description': 'Phone number',
                        'required': False,
                        'type': 'string'
                    },
                }
            },            
            {
                'name': 'sendToSupport',
                'description': 'Send a message to the support team, used for service escalation. ',
                'parameters': {
                    'custId': {
                        'description': 'customer ID',
                        'required': True,
                        'type': 'string'
                    },
                    'purchaseId': {
                        'description': 'the ID of the purchase, can be found using purchaseSearch',
                        'required': True,
                        'type': 'string'
                    },
                    'supportSummary': {
                        'description': 'Summary of the support request',
                        'required': True,
                        'type': 'string'
                    },
                }
            },
            {
                'name': 'purchaseSearch',
                'description': """Search for, and get details of a purchases made.  Details can be used for raising support requests. You can confirm you have this data, for example "I found your purchase" or "I can't find your purchase", but other details are private information and must not be given to the user.""",
                'parameters': {
                    'custId': {
                        'description': 'customer ID',
                        'required': True,
                        'type': 'string'
                    },
                    'productDescription': {
                        'description': 'a description of the purchased product to search for',
                        'required': True,
                        'type': 'string'
                    },
                    'purchaseDate': {
                        'description': 'date of purchase to start search from, in YYYY-MM-DD format',
                        'required': True,
                        'type': 'string'
                    },
                }
            }
        ]
    }
)




actionGroupId = update_agent_action_group_response['agentActionGroup']['actionGroupId']

wait_for_action_group_status(
    agentId=agentId,
    actionGroupId=actionGroupId
)

# #### Add code interpreter to deal with date
create_agent_action_group_response = bedrock_agent.create_agent_action_group(
    actionGroupName='CodeInterpreterAction',
    actionGroupState='ENABLED',
    agentId=agentId,
    agentVersion='DRAFT',
    parentActionGroupSignature='AMAZON.CodeInterpreter'
)

codeInterpreterActionGroupId = create_agent_action_group_response['agentActionGroup']['actionGroupId']

wait_for_action_group_status(
    agentId=agentId, 
    actionGroupId=codeInterpreterActionGroupId
)


# #### prepare agent and alias to add new action group
prepare_agent_response = bedrock_agent.prepare_agent(
    agentId=agentId
)

wait_for_agent_status(
    agentId=agentId,
    targetStatus='PREPARED'
)

bedrock_agent.update_agent_alias(
    agentId=agentId,
    agentAliasId=agentAliasId,
    agentAliasName='test',
)

wait_for_agent_alias_status(
    agentId=agentId,
    agentAliasId=agentAliasId,
    targetStatus='PREPARED'
)

############################################################## #  Guard Rails # ##############################################################

create_guardrail_response = bedrock_agent.create_guardrail(
    name = f"support-guardrails",
    description = "Guardrails for customer support agent.",
    topicPolicyConfig={
        'topicsConfig': [
            {
                "name": "Internal Customer Information",
                "definition": "Information relating to this or other customers that is only available through internal systems.  Such as a customer ID. ",
                "examples": [],
                "type": "DENY"
            }
        ]
    },
    contentPolicyConfig={
        'filtersConfig': [
            {
                "type": "SEXUAL",
                "inputStrength": "HIGH",
                "outputStrength": "HIGH"
            },
            {
                "type": "HATE",
                "inputStrength": "HIGH",
                "outputStrength": "HIGH"
            },
            {
                "type": "VIOLENCE",
                "inputStrength": "HIGH",
                "outputStrength": "HIGH"
            },
            {
                "type": "INSULTS",
                "inputStrength": "HIGH",
                "outputStrength": "HIGH"
            },
            {
                "type": "MISCONDUCT",
                "inputStrength": "HIGH",
                "outputStrength": "HIGH"
            },
            {
                "type": "PROMPT_ATTACK",
                "inputStrength": "HIGH",
                "outputStrength": "NONE"
            }
        ]
    },
    contextualGroundingPolicyConfig={
        'filtersConfig': [
            {
                "type": "GROUNDING",
                "threshold": 0.7
            },
            {
                "type": "RELEVANCE",
                "threshold": 0.7
            }
        ]
    },
    blockedInputMessaging = "Sorry, the model cannot answer this question.",
    blockedOutputsMessaging = "Sorry, the model cannot answer this question."
)

guardrailId = create_guardrail_response['guardrailId']
guardrailArn = create_guardrail_response['guardrailArn']

create_guardrail_version_response = bedrock_agent.create_guardrail_version(
    guardrailIdentifier=guardrailId
)

guardrailVersion = create_guardrail_version_response['version']

# ### Update the agent

agentDetails = bedrock_agent.get_agent(agentId=agentId)

bedrock_agent.update_agent(
    agentId=agentId,
    agentName=agentDetails['agent']['agentName'],
    agentResourceRoleArn=agentDetails['agent']['agentResourceRoleArn'],
    instruction=agentDetails['agent']['instruction'],
    foundationModel=agentDetails['agent']['foundationModel'],
    guardrailConfiguration={
        'guardrailIdentifier': guardrailId,
        'guardrailVersion': guardrailVersion
    }

)


# ### Prepare agent and alias

bedrock_agent.prepare_agent(
    agentId=agentId
)

wait_for_agent_status(
    agentId=agentId,
    targetStatus='PREPARED'
)

bedrock_agent.update_agent_alias(
    agentId=agentId,
    agentAliasId=agentAliasId,
    agentAliasName='MyAgentAlias',
)

wait_for_agent_alias_status(
    agentId=agentId,
    agentAliasId=agentAliasId,
    targetStatus='PREPARED'
)

########################################################### # Read the FAQ Manual # ###########################################################


describe_agent_response = bedrock_agent.get_agent(
    agentId=agentId
)

print(json.dumps(describe_agent_response, indent=4, default=str))

print(describe_agent_response['agent']['instruction'])

# ### Look at the knowledge base
get_knowledge_base_response = bedrock_agent.get_knowledge_base(
    knowledgeBaseId=knowledgeBaseId
)

print(json.dumps(get_knowledge_base_response, indent=4, default=str))

# ### Connect the knowledge base
associate_agent_knowledge_base_response = bedrock_agent.associate_agent_knowledge_base(
    agentId=agentId,
    knowledgeBaseId=knowledgeBaseId,
    agentVersion='DRAFT',
    description='my-kb'
)

# ### Prepare agent and alias

bedrock_agent.prepare_agent(
    agentId=agentId
)

wait_for_agent_status(
    agentId=agentId,
    targetStatus='PREPARED'
)

bedrock_agent.update_agent_alias(
    agentId=agentId,
    agentAliasId=agentAliasId,
    agentAliasName='MyAgentAlias',
)

wait_for_agent_alias_status(
    agentId=agentId,
    agentAliasId=agentAliasId,
    targetStatus='PREPARED'
)


# ### Try it out



sessionId = str(uuid.uuid4())
message=""""mike@mike.com - I bought a mug 10 weeks ago and now it's broken. I want a refund."""




invoke_agent_and_print(
    agentId=agentId,
    agentAliasId=agentAliasId,
    inputText=message,  
    sessionId=sessionId,
    enableTrace=False
)




message=""""It's just a minor crack.  What can I do?"""




invoke_agent_and_print(
    agentId=agentId,
    agentAliasId=agentAliasId,
    inputText=message,  
    sessionId=sessionId,
    enableTrace=True
)


# ### Another Question, new session



sessionId = str(uuid.uuid4())
message=""""My mug is chipped, what can I do?"""




invoke_agent_and_print(
    agentId=agentId,
    agentAliasId=agentAliasId,
    inputText=message,  
    sessionId=sessionId,
    enableTrace=True
)




message=""""mike@mike.com - I am not happy.  I bought this mug yesterday. I want a refund."""




invoke_agent_and_print(
    agentId=agentId,
    agentAliasId=agentAliasId,
    inputText=message,  
    sessionId=sessionId,
    enableTrace=True
)