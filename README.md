[![CircleCI](https://circleci.com/gh/numerai/submission-criteria.svg?style=svg&circle-token=eafb6c8ab5f97e310cb69134991017044321ba42)](https://circleci.com/gh/numerai/submission-criteria)

Overview
========

Server
------

The server is meant to handle requests that look like the following:

``` json
{
    "user_id": "zuz",
    "submission_id": "58d411e57278611200ee49a6",
    "api_key": "h/52y/E7cm8Ih4F3cVdlBM4ZQxER+Apk6P0L7yR0lFU="
}
```

From there it will ensure that there is an API key for authentication and then queue the requests to the leaderboard\_queue. That is then processed by another thread that pushes the submission to a concordance\_queue and a originality queue. Those can then calculate the concordance and originality of the submission and update the submission in DB. This pipeline is to ensure that the submission requests are processed in a timely fashion.

Concordance
-----------

There is a separate thread that consumes from the concordance\_queue and calculates the concordance for a submission request. We pull the competition data from a designated S3 bucket and calculate the K-Means clustering. From there we pull the submission data from our DB and calculate the concordance using Two-Sample Kolmogorov-Smirnov statistic. Once we have calculated that we update the submission entry in DB with the concordance result.

Originality
-----------

There is a separate thread that consumes from the originality\_queue and calculates the originality for a submission request. For the originality score we have to pull all previous submissions for the current competition round and calculate the Two-Sample Kolmogorov-Smirnov score between the submission and all other previous submissions.

If one of the scores falls under a specific threshold it is deemed to be identical to a previous submission is not considered original. Else if it falls under another threshold the submission is considered to be 'similar' and is counted against the submission. After we have compared the submission against all previous ones we check the count of how many submissions the current submission was similar to. If that is greater than a max limit then the model is considered to not be original.

It follows this pseudo-code:

    var curr_submission, similar_count = 0, max_similar = 1

    for submission in get_previous_submissions(curr_submission['date_created']):
        var ks_score = two_sample_ks(curr_submission, sub)
        if ks_score < equal_threshold:
            not_original
        else if ks_score < similar_threshold:
            similar_count += 1

    if similar_count >= max_similar:
        not_original
    else:
        original

Once we have determined if a submission is original or not we then update our submission in DB with the originality result.

Running the server
==================

First off you will need to install all of the requirements for the server to run. It is recommended that you use `pip` to do so.

If you do not have `pip` installed to can find the instructions [here](https://pip.pypa.io/en/stable/installing/).

    $ pip install -r requirements.txt # you can also use the --requirement flag

To start a **PRODUCTION** server it will require the sourcing environment variables and you can do so using a script such as the following:

``` bash
#!/bin/bash
export S3_ACCESS_KEY=<YOUR_S3_ACCESS_KEY>
export S3_SECRET_KEY=<YOUR_S3_SECRET_KEY>
export PORT=<YOUR_PORT>
export API_KEY=<YOUR_API_KEY>
```

NOTE: You will need to replace all values in the `<>` with appropriate values.

If you are just running the server locally for development purposes you will not need to source the above variables to you environment.

Once you have installed the requirements and sourced the needed variables you can run the server.

    $ ./server


Test the server:
``` bash
curl -vv -H "Content-Type: application/json" -X POST -d '{"submission_id": "7496e75d-8be1-445f-8883-9f565d9a7244", "api_key": "h/52y/E7cm8Ih4F3cVdlBM4ZQxER+Apk6P0L7yR0lFU="}' 'http://localhost:5151/'
```

Deployment
==========
- Create Elastic Beanstalk environemnt: `./deploy/new-environment.sh api-ml-production api-ml-production`
- Create a new environment: `./deploy/gen-dockerrun.sh prod && ./deploy/new-environment.sh api-ml-production api-ml-production`
- Deploy changes: `./deploy/push.sh prod api-ml-production`

Community
=========

For questions or discussion about the code, either file an issue or join our [Slack](https://slack.numer.ai/).

Bounty rules
============

What bounties?
--------------

See [this Medium post](https://medium.com/numerai/open-sourcing-model-evaluation-on-numerai-295c1ea3d001).

How will I receive my bounty?
-----------------------------

When you create the pull request, you must specify one or more usernames where the bounty will be sent. We will only send the bounty directly to user accounts. If you would like to hold your NMR somewhere else, you may withdraw it from your account.

Who will get the bounty if multiple people complete the same task?
------------------------------------------------------------------

If multiple people independently complete the same task, the first pull request that is approved will receive the bounty. We will accept the pull request that is code complete first, as determined by the timestamp of pull request or the *last* commit in the branch, whichever is later.

For example, suppose Alice and Bob are solving a task with a bounty, and Alice creates a pull request first, then Bob creates one. If Alice's pull request is approved with no changes, then she will receive the bounty. If, however, we request changes to Alice's PR, but Bob's is good to go, then Bob will receive the bounty. If both require changes, then whoever completes those changes first will get the bounty.

I promise I'm going to complete this task next week, can I claim it so that nobody finishes before me?
------------------------------------------------------------------------------------------------------

We do not allow users to claim tasks; bounties will be paid on a first-come, first-served basis. It may be advisable to let others know if you're working on an issue (for example, by commenting on the issue), but this is not required.

Since we may occasionally remove bounties if the changes are no longer necessary, you may wish to let us know you're working on the issue (publicly or privately). If you are actively working on an issue, we will generally not remove the bounty.

Finally, if you submit a pull request that we intend to approve, but we ask for a few small changes (e.g. formatting), we may explicitly temporarily "hold" the bounty for you, where if you complete the changes promptly, we will not give the bounty to anyone else.

What if I work together with someone to complete a task, and we would like to split the bounty?
-----------------------------------------------------------------------------------------------

Whoever makes the pull request needs to specify *in the pull request* how they would like the bounty split among users.

My pull request is awesome, but you guys won't approve it!
----------------------------------------------------------

Pull requests will be approved our Numerai's sole discretion. Bounties will be paid out only for approved pull requests.

I want to work on something, but there's no bounty for it.
----------------------------------------------------------

That's great, go ahead and work on it! Most potential improvements do not have bounties, but that doesn't mean they shouldn't be completed!

Can I make a pull request for these rules?
------------------------------------------

Yes.
