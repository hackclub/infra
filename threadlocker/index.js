require('dotenv').config()
const { App } = require('@slack/bolt');
const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();
const Sentry = require("@sentry/node");
const { nodeProfilingIntegration } = require("@sentry/profiling-node")
const app = new App({
    token: process.env.SLACK_BOT_TOKEN,
    socketMode: true,
    appToken: process.env.SLACK_APP_TOKEN,
    signingSecret: process.env.SLACK_SIGNING_SECRET
});

Sentry.init({
    dsn: process.env.SENTRY_DSN,
    integrations: [
        nodeProfilingIntegration(),
        new Sentry.Integrations.Prisma({ prisma })
    ],
    tracesSampleRate: 1.0,
    profilesSampleRate: 1.0,
});


(async () => {
    async function autoUnlock() {
        let span;
        if (process.env.SENTRY_DSN) span = Sentry.startInactiveSpan({ name: "unlock_thread_cron" });
        // Automatic unlocking, checks database once per minute
        const threads = await prisma.thread.findMany({
            where: {
                time: {
                    lte: new Date()
                },
                active: true
            }
        })
        threads.forEach(async thread => {
            await app.client.chat.postMessage({ // Inform the user that the thread is currently locked. Do this first because deleting the message may not work.
                channel: thread.channel,
                thread_ts: thread.id,
                text: "🔓 Thread unlocked as enough time has passed."
            })
            await app.client.chat.postMessage({
                channel: process.env.SLACK_LOG_CHANNEL,
                text: `🔓 Thread unlocked in <#${thread.channel}>
Reason: Autounlock (triggered by cron job)
Admin: System
Link: https://hackclub.slack.com/archives/${thread.channel}/p${thread.id.toString().replace(".", "")}`
            })
            try {
                await app.client.reactions.remove({ // Remove lock reaction
                    channel: thread.channel,
                    name: "lock",
                    timestamp: thread.id
                })
            } catch (e) {

            }
            await prisma.thread.update({ // Delete record from database
                where: {
                    id: thread.id
                },
                data: {
                    active: false
                }
            })

        })
        if (process.env.SENTRY_DSN) span.end()
    }
    setInterval(autoUnlock, 1000 * 60)
    app.view('lock_modal', async ({ view, ack, body, respond }) => {
        let span;
        if (process.env.SENTRY_DSN) span = Sentry.startInactiveSpan({ name: "lock_thread" });
        try {
            var json = JSON.parse(view.private_metadata)
        } catch (e) {
            await ack()
            return respond("Something bad happened. Likely more than one instance is running.")
        }
        const thread_id = json.thread_id
        const channel_id = json.channel_id

        const submittedValues = view.state.values
        let reason, expires;

        for (let key in submittedValues) {
            if (submittedValues[key]['plain_text_input-action']) reason = submittedValues[key]['plain_text_input-action'].value
            if (submittedValues[key]['datetimepicker-action']) expires = new Date(submittedValues[key]['datetimepicker-action'].selected_date_time * 1000)
        }

        if (!reason) return await ack({
            "response_action": "errors",
            errors: {
                "datetimepicker-action": "Please provide a reason."
            }
        });
        if (new Date() > expires) return await ack({
            "response_action": "errors",
            errors: {
                "datetimepicker-action": "Time cannot be in the past."
            }
        });
        await ack()
        const thread = await prisma.thread.findFirst({
            where: {
                id: thread_id
            }
        })
        if (!thread) {
            await prisma.thread.create({ // Add thread lock to database
                data: {
                    id: thread_id,
                    admin: body.user.id,
                    lock_type: "test",
                    time: expires,
                    reason,
                    channel: channel_id,
                    active: true
                }
            })
        } else {
            await prisma.thread.update({ // Update thread lock in database
                where: {
                    id: thread_id
                },
                data: {
                    id: thread_id,
                    admin: body.user.id,
                    lock_type: "test",
                    time: expires,
                    reason,
                    channel: channel_id,
                    active: true
                }
            })
        }

        await app.client.chat.postMessage({ // Inform users in the thread that it is locked
            channel: channel_id,
            thread_ts: thread_id,
            text: `🔒 Thread locked by <@${body.user.id}>. Reason: ${reason} (until: ${expires.toLocaleString('en-US', { timeZone: 'America/New_York', timeStyle: "short", dateStyle: "long" })} EST)`,

        })

        await app.client.chat.postMessage({
            channel: process.env.SLACK_LOG_CHANNEL,
            text: `🔒 Thread locked in <#${channel_id}>
Reason: ${reason}
Admin: <@${body.user.id}>
Expires: ${expires.toLocaleString('en-US', { timeZone: 'America/New_York', timeStyle: "short", dateStyle: "long" })} (EST)
Link: https://hackclub.slack.com/archives/${channel_id}/p${thread_id.toString().replace(".", "")}`
        })

        try {
            await app.client.reactions.add({ // Add lock reaction
                channel: channel_id,
                name: "lock",
                timestamp: thread_id
            })
        } catch (e) {

        }
        if (process.env.SENTRY_DSN) span.end()
    });

    app.message(/.*/gim, async ({ message, say, body, }) => { // Listen for all messages (/.*/gim is a regex)

        if (!message.thread_ts) return // Return if not a thread
        const thread = await prisma.thread.findFirst({
            where: {
                id: message.thread_ts
            }
        }) // Lookup and see if the thread is locked in the dataase
        if (!thread) return
        try {
            if (thread.active && thread.time > new Date()) {

                const user = await app.client.users.info({ user: message.user })
                if (!user.user.is_admin) {
                    let span;
                    if (process.env.SENTRY_DSN) span = Sentry.startInactiveSpan({ name: "delete_message" });
                    await app.client.chat.postEphemeral({ // Inform the user that the thread is currently locked. Do this first because deleting the message may not work.
                        user: message.user,
                        channel: message.channel,
                        thread_ts: message.thread_ts,
                        text: `Sorry, the thread is currently locked until ${thread.time.toLocaleString('en-US', { timeZone: 'America/New_York', timeStyle: "short", dateStyle: "long" })} EST`
                    })

                    await app.client.chat.delete({ // Delete the chat message 
                        channel: message.channel,
                        ts: message.ts,
                        token: process.env.SLACK_USER_TOKEN
                    })
                    if (process.env.SENTRY_DSN) span.end()
                }
            } else if (thread.active && thread.time < new Date()) {
                let span;
                if (process.env.SENTRY_DSN) span = Sentry.startInactiveSpan({ name: "unlock_thread_message" });
                await app.client.chat.postMessage({ // Inform the user that the thread is currently locked. Do this first because deleting the message may not work.
                    channel: message.channel,
                    thread_ts: message.thread_ts,
                    text: "🔓 Thread unlocked as enough time has passed."
                })

                await app.client.chat.postMessage({
                    channel: process.env.SLACK_LOG_CHANNEL,
                    text: `🔓 Thread unlocked in <#${message.channel}>
Reason: Autounlock (triggered by message)
Admin: System
Link: https://hackclub.slack.com/archives/${thread.channel}/p${thread.id.toString().replace(".", "")}`
                })

                await prisma.thread.update({ // Delete record from database
                    where: {
                        id: message.thread_ts
                    },
                    data: {
                        active: false
                    }
                })

                await app.client.reactions.remove({ // Remove lock reaction
                    channel: message.channel,
                    name: "lock",
                    timestamp: message.thread_ts
                })
                if (process.env.SENTRY_DSN) span.end()
            }
        } catch (e) {
            // Insufficent permissions, most likely.
            // An admin MUST authorise the bot.
            console.error(e)

        }

    });

    app.shortcut('lock_thread', async ({ ack, body, say, client, respond }) => {         // This listens for the "lock thread shortcut"
        await ack();
        const user = await app.client.users.info({ user: body.user.id })

        if (!body.message.thread_ts) return await client.chat.postEphemeral({
            channel: body.channel.id,
            user: body.user.id,
            text: "❌ This is not a thread"
        })
        if (process.env.NODE_ENV == "production" && !user.user.is_admin)
            return await client.chat.postEphemeral({
                channel: body.channel.id,
                user: body.user.id,
                thread_ts: body.message.thread_ts,
                text: "❌ Only admins can run this command."
            })


        const thread = await prisma.thread.findFirst({ // Look up in the database if it exists
            where: {
                id: body.message.thread_ts
            }
        })
        if (!thread || !thread.active) {
            const modal = require("./utils/modal.json");

            return await client.views.open({
                trigger_id: body.trigger_id,
                view: {
                    ...require("./utils/modal.json"), callback_id: "lock_modal", private_metadata: JSON.stringify({
                        thread_id: body.message.thread_ts, channel_id: body.channel.id
                    })
                }
            })
        }
        else {
            let span;
            if (process.env.SENTRY_DSN) span = Sentry.startInactiveSpan({ name: "unlock_thread_admin" });
            await prisma.thread.update({ // Update from database
                where: {
                    id: body.message.thread_ts
                },
                data: {
                    active: false,
                },
            })
            await app.client.chat.postMessage({ // Inform users in the thread that it is unlocked
                channel: body.channel.id,
                thread_ts: body.message.thread_ts,
                text: `🔓 Thread unlocked by <@${body.user.id}>`
            })
            await app.client.chat.postMessage({
                channel: process.env.SLACK_LOG_CHANNEL,
                text: `🔓 Thread unlocked in <#${body.channel.id}>
Reason: Admin clicked unlock.
Admin: <@${body.user.id}>
Link: https://hackclub.slack.com/archives/${body.channel.id}/p${body.message.thread_ts.toString().replace(".", "")}`
            })

            try {
                await app.client.reactions.remove({ // Remove lock reaction
                    channel: body.channel.id,
                    name: "lock",
                    timestamp: body.message.thread_ts
                })
            } catch (e) { }
            if (process.env.SENTRY_DSN) span.end()
        }
        return
    })

    const envs = [
        'DATABASE_URL',
        'SLACK_BOT_TOKEN',
        'SLACK_APP_TOKEN',
        'SLACK_SIGNING_SECRET',
        'SLACK_USER_TOKEN'
    ];

    envs.forEach((env) => {
        if (!process.env[env]) {
            console.error(`(fatal error) Please set the ${env} environment variable`);
            process.exit(1);
        }
    });
    await app.start();
    console.log('Threadlocker is running!');

    if (process.env.NODE_ENV != "production") console.info("\u{2139}\u{FE0F} Please note: Threadlocker is in development mode.")
    await autoUnlock()

})();

process.on("unhandledRejection", (error) => {
    console.error(error);
});