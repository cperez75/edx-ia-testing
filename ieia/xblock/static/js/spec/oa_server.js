import Server from 'oa_server';
/*
Tests for OA XBlock server interactions.
*/

describe("ieia.Server", function() {

    // Stub runtime implementation that returns the handler as the URL
    var runtime = {
        handlerUrl: function(element, handler) { return "/" + handler; }
    };

    let server = null;

    var jsonContentType = "application/json; charset=utf-8";

    /**
    Stub AJAX requests.

    Args:
        success (bool): If true, return a promise that resolves;
            otherwise, return a promise that fails.

        responseData(object): Data to pass to the caller if the AJAX
            call completes successfully.
    **/
    var stubAjax = function(success, responseData) {
        spyOn($, 'ajax').and.returnValue(
            $.Deferred(function(defer) {
                if (success) { defer.resolveWith(this, [responseData]); }
                else { defer.reject(); }
           }).promise()
        );
    };

    var PROMPTS = [{"description": "Hello this is the prompt yes."}];
    var FEEDBACK_PROMPT = "Prompt for feedback";
    var FEEDBACK_DEFAULT_TEXT = "Default feedback response text";

    var RUBRIC = '<rubric>'+
        '<criterion>'+
            '<name>𝓒𝓸𝓷𝓬𝓲𝓼𝓮</name>'+
            '<prompt>How concise is it?</prompt>'+
            '<option points="3">'+
                '<name>ﻉซƈﻉɭɭﻉกՇ</name>'+
                '<explanation>Extremely concise</explanation>'+
            '</option>'+
            '<option points="2">'+
                '<name>Ġööḋ</name>'+
                '<explanation>Concise</explanation>'+
            '</option>'+
            '<option points="1">'+
                '<name>ק๏๏г</name>'+
                '<explanation>Wordy</explanation>'+
            '</option>'+
        '</criterion>'+
    '</rubric>';

    var RUBRIC_JSON = {
        "criteria": [
            {
                "label": "𝓒𝓸𝓷𝓬𝓲𝓼𝓮",
                "prompt": "How concise is it?",
                "feedback": "disabled",
                "options": [
                    {
                        "label": "ﻉซƈﻉɭɭﻉกՇ",
                        "points": 3,
                        "explanation": "Extremely concise",
                        "name": "",
                        "order_num": 0
                    },
                    {
                        "label": "Ġööḋ",
                        "points": 2,
                        "explanation": "Concise",
                        "name": "",
                        "order_num": 1
                    },
                    {
                        "label": "ק๏๏г",
                        "points": 1,
                        "explanation": "Wordy",
                        "name": "",
                        "order_num": 2
                    }
                ],
                "name": "Ideas",
                "order_num": 0
            },
        ],
        "feedback_prompt": "Feedback instruction ...",
        "feedback_default_text": "Feedback default text\n"
    }

    var CRITERIA = [
        'criteria',
        'objects',
        'would',
        'be',
        'here'
    ];

    var ASSESSMENTS = [
        {
            "name": "peer-assessment",
            "must_grade": 5,
            "must_be_graded_by": 3,
            "start": "",
            "due": "4014-03-10T00:00:00"
        },
        {
            "name": "self-assessment",
            "start": "",
            "due": ""
        }
    ];

    var EDITOR_ASSESSMENTS_ORDER = [
        "student_training",
        "peer_assessment",
        "self_assessment",
    ];

    var TITLE = 'This is the title.';
    var SUBMISSION_START = '2012-10-09T00:00:00';
    var SUBMISSION_DUE = '2015-10-10T00:00:00';
    var DATE_CONFIG_TYPE = "manual"

    beforeEach(function() {
        // Create the server
        // Since the runtime is a stub implementation that ignores the element passed to it,
        // we can set the element parameter to null.
        server = new Server(runtime, null);
    });

    it("renders the XBlock as HTML", function() {
        stubAjax(true, "<div>Open Assessment</div>");

        var loadedHtml = "";
        server.render('submission').done(function(html) {
            loadedHtml = html;
        });

        expect(loadedHtml).toEqual("<div>Open Assessment</div>");
        expect($.ajax).toHaveBeenCalledWith({
            url: '/render_submission', type: "POST", dataType: "html"
        });
    });

    it("sends a submission to the XBlock", function() {
        // Status, student ID, attempt number
        stubAjax(true, [true, 1, 2]);

        var receivedStudentId = null;
        var receivedAttemptNum = null;
        server.submit("This is only a test").done(
            function(studentId, attemptNum) {
                receivedStudentId = studentId;
                receivedAttemptNum = attemptNum;
            }
        );

        expect(receivedStudentId).toEqual(1);
        expect(receivedAttemptNum).toEqual(2);
        expect($.ajax).toHaveBeenCalledWith({
            url: '/submit',
            type: "POST",
            data: JSON.stringify({submission: "This is only a test"}),
            contentType : jsonContentType
        });
    });

    it("sends a submission to XBlock for cancellation", function() {
        stubAjax(true, {success:true, msg:'test message'});

        var submissionUUID = 'Bob';
        var comments = 'Cancellation reason.';
        var success = false;
        server.cancelSubmission(submissionUUID, comments).done(
            function() {
                success=true;
            }
        );

        expect(success).toBe(true);
        expect($.ajax).toHaveBeenCalledWith({
            url: '/cancel_submission',
            type: "POST",
            data: JSON.stringify({submission_uuid: submissionUUID, comments: comments}),
            contentType : jsonContentType
        });
    });

    it("saves a response submission", function() {
        stubAjax(true, {'success': true, 'msg': ''});
        var success = false;
        server.save("Test").done(function() { success = true; });
        expect(success).toBe(true);
        expect($.ajax).toHaveBeenCalledWith({
            url: "/save_submission",
            type: "POST",
            data: JSON.stringify({submission: "Test"}),
            contentType : jsonContentType
        });
    });

    it("saves files descriptions", function() {
        stubAjax(true, {'success': true, 'msg': ''});
        var success = false;
        server.saveFilesDescriptions([{description: 'test1', fileName: 'fileName1'},
            {description: 'test2', fileName: 'fileName2'}]).done(function() { success = true; });
        expect(success).toBe(true);
        expect($.ajax).toHaveBeenCalledWith({
            url: "/save_files_descriptions",
            type: "POST",
            data: JSON.stringify({fileMetadata: [{description: 'test1', fileName: 'fileName1'},
            {description: 'test2', fileName: 'fileName2'}]}),
            contentType : jsonContentType
        });
    });

    it("sends a peer-assessment to the XBlock", function() {
        stubAjax(true, {success: true, msg: ''});

        var success = false;
        var options = {clarity: "Very clear", precision: "Somewhat precise"};
        var criterionFeedback = {clarity: "This essay was very clear."};
        server.peerAssess(options, criterionFeedback, "Excellent job!").done(
            function() { success = true; }
        );

        expect(success).toBe(true);
        expect($.ajax).toHaveBeenCalledWith({
            url: '/peer_assess',
            type: "POST",
            data: JSON.stringify({
                options_selected: options,
                criterion_feedback: criterionFeedback,
                overall_feedback: "Excellent job!"
            }),
            contentType : jsonContentType
        });
    });

    it("sends a self-assessment to the XBlock", function() {
        stubAjax(true, {success: true, msg: ''});

        var success = false;
        var options = {clarity: "Very clear", precision: "Somewhat precise"};
        var criterionFeedback = {clarity: "This essay was very clear."};
        server.selfAssess(options, criterionFeedback, "Excellent job!").done(
            function() { success = true; }
        );

        expect(success).toBe(true);
        expect($.ajax).toHaveBeenCalledWith({
            url: '/self_assess',
            type: "POST",
            data: JSON.stringify({
                options_selected: options,
                criterion_feedback: criterionFeedback,
                overall_feedback: "Excellent job!"
            }),
            contentType : jsonContentType
        });

    });

    it("sends a training assessment to the XBlock", function() {
        stubAjax(true, {success: true, msg: '', correct: true});
        var success = false;
        var corrections = null;
        var options = {clarity: "Very clear", precision: "Somewhat precise"};
        server.trainingAssess(options).done(
            function(result) {
                success = true;
                corrections = result;
            }
        );

        expect(success).toBe(true);
        expect(corrections).toBeUndefined();
        expect($.ajax).toHaveBeenCalledWith({
            url: '/training_assess',
            type: "POST",
            data: JSON.stringify({
                options_selected: options
            }),
            contentType : jsonContentType
        });
    });

    it("Sends feedback on an assessment to the XBlock", function() {
        stubAjax(true, {success: true, msg: ''});

        var success = false;
        var options = ["Option 1", "Option 2"];
        server.submitFeedbackOnAssessment("test feedback", options).done(function() {
            success = true;
        });

        expect(success).toBe(true);
        expect($.ajax).toHaveBeenCalledWith({
            url: '/submit_feedback',
            type: "POST",
            data: JSON.stringify({
                feedback_text: "test feedback",
                feedback_options: options
            }),
            contentType : jsonContentType
        });
    });

    it("updates the XBlock's editor context definition", function() {
        stubAjax(true, { success: true });
        server.updateEditorContext({
            prompts: PROMPTS,
            feedbackPrompt: FEEDBACK_PROMPT,
            feedback_default_text: FEEDBACK_DEFAULT_TEXT,
            title: TITLE,
            submissionStart: SUBMISSION_START,
            submissionDue: SUBMISSION_DUE,
            dateConfigType: DATE_CONFIG_TYPE,
            criteria: CRITERIA,
            assessments: ASSESSMENTS,
            editorAssessmentsOrder: EDITOR_ASSESSMENTS_ORDER,
            fileUploadType: "image",
            fileTypeWhiteList: ['pdf', 'doc'],
            multipleFilesEnabled: true,
            latexEnabled: true,
            leaderboardNum: 15
        });
        expect($.ajax).toHaveBeenCalledWith({
            type: "POST", url: '/update_editor_context',
            data: JSON.stringify({
                prompts: PROMPTS,
                feedback_prompt: FEEDBACK_PROMPT,
                feedback_default_text: FEEDBACK_DEFAULT_TEXT,
                title: TITLE,
                submission_start: SUBMISSION_START,
                submission_due: SUBMISSION_DUE,
                date_config_type: DATE_CONFIG_TYPE,
                criteria: CRITERIA,
                assessments: ASSESSMENTS,
                editor_assessments_order: EDITOR_ASSESSMENTS_ORDER,
                file_upload_type: "image",
                white_listed_file_types: ['pdf', 'doc'],
                allow_multiple_files: true,
                allow_latex: true,
                leaderboard_show: 15
            }),
            contentType : jsonContentType
        });
    });

    it("Checks whether the XBlock has been released", function() {
        stubAjax(true, { success: true, is_released: true });

        var receivedIsReleased = null;
        server.checkReleased().done(function(isReleased) {
            receivedIsReleased = isReleased;
        });

        expect(receivedIsReleased).toBe(true);
        expect($.ajax).toHaveBeenCalledWith({
            url: '/check_released', type: "POST", data: "\"\"",
            contentType : jsonContentType
        });
    });

    it("verifies that publishing an event submits the correct data to the backend", function() {
        stubAjax(true, {success: true});
        server.publishEvent('test_event_name', {'key': 'test_data'});

        expect($.ajax).toHaveBeenCalledWith({
            url: '/publish_event',
            type: 'POST',
            data: JSON.stringify({'key': 'test_data', 'event_name': 'test_event_name'}),
            contentType: jsonContentType
        });
    });

    it("informs the caller of an Ajax error when rendering as HTML", function() {
        stubAjax(false, null);

        var receivedMsg = "";
        server.render('submission').fail(function(msg) {
            receivedMsg = msg;
        });

        expect(receivedMsg).toContain("This section could not be loaded");
    });

    it("informs the caller of an Ajax error when sending a submission", function() {
        stubAjax(false, null);

        var receivedErrorCode = "";
        var receivedErrorMsg = "";
        server.submit('This is only a test.').fail(
            function(errorCode, errorMsg) {
                receivedErrorCode = errorCode;
                receivedErrorMsg = errorMsg;
            }
        );

        expect(receivedErrorCode).toEqual("AJAX");
        expect(receivedErrorMsg).toContain("This response could not be submitted");
    });

    it("informs the caller of an server error when sending a submission", function() {
        stubAjax(true, [false, "ENODATA", "Error occurred!"]);

        var receivedErrorCode = "";
        var receivedErrorMsg = "";
        server.submit('This is only a test.').fail(
            function(errorCode, errorMsg) {
                receivedErrorCode = errorCode;
                receivedErrorMsg = errorMsg;
            }
        );

        expect(receivedErrorCode).toEqual("ENODATA");
        expect(receivedErrorMsg).toEqual("Error occurred!");
    });

    it("informs the caller of an AJAX error when saving a submission", function() {
        stubAjax(false, null);
        var receivedMsg = null;
        server.save("Test").fail(function(errorMsg) { receivedMsg = errorMsg; });
        expect(receivedMsg).toContain('Please check your internet connection');
    });

    it("informs the caller of an AJAX error when sending a self assessment", function() {
        stubAjax(false, null);
        var receivedMsg = null;
        server.selfAssess("Test", {}, "Excellent job!").fail(function(errorMsg) { receivedMsg = errorMsg; });
        expect(receivedMsg).toContain('This assessment could not be submitted');
    });

    it("informs the caller of a server error when sending a submission", function() {
        stubAjax(true, {'success': false, 'msg': 'test error'});
        var receivedMsg = null;
        server.save("Test").fail(function(errorMsg) { receivedMsg = errorMsg; });
        expect(receivedMsg).toEqual('test error');
    });

    it("informs the caller of an Ajax error when updating the editor context", function() {
        stubAjax(false, null);

        var receivedMsg = null;
        server.updateEditorContext('prompt', 'rubric', 'title', 'start', 'due', 'assessments').fail(function(msg) {
            receivedMsg = msg;
        });

        expect(receivedMsg).toContain("This problem could not be saved");
    });

    it("informs the caller of a server error when loading the editor context", function() {
        stubAjax(true, { success: false, msg: "Test error" });

        var receivedMsg = null;
        server.updateEditorContext('prompt', 'rubric', 'title', 'start', 'due', 'assessments').fail(function(msg) {
            receivedMsg = msg;
        });

        expect(receivedMsg).toEqual("Test error");
    });

    it("informs the caller of a server error when sending a peer assessment", function() {
        stubAjax(true, {success:false, msg:'Test error!'});

        var receivedMsg = null;
        var options = {clarity: "Very clear", precision: "Somewhat precise"};
        server.peerAssess(options, {}, "Excellent job!").fail(function(msg) {
            receivedMsg = msg;
        });

        expect(receivedMsg).toEqual("Test error!");
    });

    it("informs the caller of an AJAX error when sending a peer assessment", function() {
        stubAjax(false, null);

        var receivedMsg = null;
        var options = {clarity: "Very clear", precision: "Somewhat precise"};
        server.peerAssess(options, {}, "Excellent job!").fail(function(msg) {
            receivedMsg = msg;
        });

        expect(receivedMsg).toContain("This assessment could not be submitted");
    });

    it("informs the caller of a server error when sending a training example assessment", function() {
        stubAjax(true, {success: false, msg: "Test error!"});
        var receivedMsg = null;
        var options = {clarity: "Very clear", precision: "Somewhat precise"};
        server.trainingAssess(options).fail(function(msg) {
            receivedMsg = msg;
        });
        expect(receivedMsg).toEqual("Test error!");
    });

    it("informs the caller of an AJAX error when sending a training example assessment", function() {
        stubAjax(false, null);

        var receivedMsg = null;
        var options = {clarity: "Very clear", precision: "Somewhat precise"};
        server.trainingAssess(options).fail(function(msg) {
            receivedMsg = msg;
        });

        expect(receivedMsg).toContain("This assessment could not be submitted");
    });

    it("informs the caller of an AJAX error when checking whether the XBlock has been released", function() {
        stubAjax(false, null);

        var receivedMsg = null;
        server.checkReleased().fail(function(errMsg) {
            receivedMsg = errMsg;
        });

        expect(receivedMsg).toContain("The server could not be contacted");

    });

    it("informs the caller of a server error when checking whether the XBlock has been released", function() {
        stubAjax(true, { success: false, msg: "Test error" });

        var receivedMsg = null;
        server.checkReleased().fail(function(errMsg) {
            receivedMsg = errMsg;
        });

        expect(receivedMsg).toEqual("Test error");
    });

    it("informs the caller of an AJAX error when sending feedback on submission", function() {
        stubAjax(false, null);

        var receivedMsg = null;
        var options = ["Option 1", "Option 2"];
        server.submitFeedbackOnAssessment("test feedback", options).fail(
            function(errMsg) { receivedMsg = errMsg; }
        );
        expect(receivedMsg).toContain("This feedback could not be submitted");
    });

    it("informs the caller of a server error when sending feedback on submission", function() {
        stubAjax(true, { success: false, msg: "Test error" });

        var receivedMsg = null;
        var options = ["Option 1", "Option 2"];
        server.submitFeedbackOnAssessment("test feedback", options).fail(
            function(errMsg) { receivedMsg = errMsg; }
        );
        expect(receivedMsg).toEqual("Test error");
    });

    it('listTeams returns team from team listing endpoint', function(){
        var expectedTeam = {name: 'TeamName', id:'TeamId'}
        stubAjax(true, {count: 1, results:[expectedTeam]});
        var receivedTeam = null;
        server.listTeams('username', 'CourseId').done(function(team) {receivedTeam = team})
        expect(receivedTeam).toEqual(expectedTeam);
    });

    it('listTeams error response from team listing endpoint', function(){
        stubAjax(false, null);
        var receivedMsg = null;
        server.listTeams('username', 'CourseId').fail(function(errMsg) {receivedMsg = errMsg;});
        expect(receivedMsg).toEqual('Could not load teams information.');
    });

    it('listTeams handles zero teams from teams listing endpoint', function(){
        stubAjax(true, {count: 0, results: []});
        var receivedVal = null;
        server.listTeams('username', 'CourseId').done(function(val){receivedVal = val;});
        expect(receivedVal).toBeNull();
    });

    it('listTeams handles multiple teams from teams listing endpoint', function(){
        stubAjax(
            true,
            {
                count: 2,
                results: [
                    {name: 'TeamName', id:'TeamId'},
                    {name: 'Team2', id: 'Team2'},
                ]
            }
        );
        var receivedMsg = null;
        server.listTeams('username', 'CourseId').fail(function(errMsg){receivedMsg = errMsg;});
        expect(receivedMsg).toEqual('Multiple teams returned for course');
    });

    it("getTeamDetail returns team detail information", function() {
        var expectedTeamDetail = {
            course_id: 'CourseID',
            description: "A team!",
            membership: [{user: {username: 'user1'}}, {user: {username: 'user1'}}, {user: {username: 'user1'}}]
        }
        stubAjax(true, expectedTeamDetail);
        let receivedDetail = null
        server.getTeamDetail('team id').done(function(teamDetail) {receivedDetail = teamDetail})
        expect(receivedDetail).toEqual(expectedTeamDetail)
    });

    it("getTeamDetail handles error response from team detail endpoint", function() {
        stubAjax(false, null);
        var promiseFailed = false;
        server.getTeamDetail('team id').fail(function() {promiseFailed = true});
        expect(promiseFailed).toBe(true)
    });

    it("getUsername handles error response from the endpoint", function() {
        stubAjax(false, null);
        var receivedMsg = "";
        server.getUsername().fail(function(msg) {receivedMsg = msg});
        expect(receivedMsg).toEqual('Error when looking up username')
    });

    it("getUsername handles null username", function() {
        stubAjax(true, {username: null});
        var receivedMsg = "";
        server.getUsername().fail(function(msg) {receivedMsg = msg});
        expect(receivedMsg).toEqual('User lookup failed')
    });

    it("getUsername returns username", function() {
        var expectedUsername = 'expected-username'
        stubAjax(true, {username: expectedUsername});
        var receivedUsername = "";
        server.getUsername().done(function(username) {receivedUsername = username});
        expect(receivedUsername).toEqual(expectedUsername)
    });

    describe('cloneRubric', () => {
        it('extracts rubric data from a successful request', () => {
            let returnedData,
                expectedData = RUBRIC_JSON;
            stubAjax(true, { success: true, rubric: RUBRIC_JSON});
            server.cloneRubric().done((data) => { returnedData = data });
            expect(returnedData).toEqual(expectedData);
        });

        it('returns error messages for known failures', () => {
            let returnedData,
                errorMsg = 'Danger, Will Robinson!';
            stubAjax(true, { success: false, msg: errorMsg});
            server.cloneRubric().fail((data) => { returnedData = data });
            expect(returnedData).toEqual(errorMsg);
        });

        it('returns a boilerplate message on other failures', () => {
            stubAjax(false, null);
            let returnedMessage = "";
            server.cloneRubric().fail((msg) => { returnedMessage = msg });
    
            expect(returnedMessage).toContain('Failed to clone rubric')
        })
    })
});
