create table if not exists capsules (
    id integer primary key autoincrement,
    song text,
    artist text,
    url text,
    site text,
    thumbnail text,
    mood text not null,
    note text not null,
    author text not null,
    source text not null check (source in ('starter', 'community')),
    status text not null default 'visible' check (status in ('visible', 'held', 'hidden', 'crisis')),
    moderation text not null default '',
    submitter text not null default '',
    created_at text not null
);

insert into capsules (song, artist, mood, note, author, source, created_at) values ('Happy', 'Pharrell Williams', 'joyful', 'For days when the good news finally lands and you want a song that matches the grin.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Walking on Sunshine', 'Katrina and the Waves', 'joyful', 'Celebration energy. Results came out, the job came through, turn it all the way up.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Good as Hell', 'Lizzo', 'joyful', 'For when you feel great about yourself and want a song that agrees with you.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Gallan Goodiyaan', 'Shankar-Ehsaan-Loy', 'joyful', 'Family-wedding happiness in one track. Best shared with friends on a good day.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Mr. Blue Sky', 'Electric Light Orchestra', 'joyful', 'The sun is out after a long grey stretch, and everything feels easy again.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Dancing Queen', 'ABBA', 'joyful', 'Pure joy for a dance in your room, no audience needed.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Someone Like You', 'Adele', 'sad', 'For a breakup that still hurts, when you need to cry it out properly.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Fix You', 'Coldplay', 'sad', 'When something you tried hard at didn''t work out and you feel heavy and lost.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Channa Mereya', 'Arijit Singh', 'sad', 'Heartbreak when you have to let someone you love go. It sits with you in the sadness.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Liability', 'Lorde', 'sad', 'For feeling like too much for the people around you. A quiet, honest kind of sad.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Hurt', 'Johnny Cash', 'sad', 'Grief and regret, slow and raw. For the nights when everything aches.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('The Night We Met', 'Lord Huron', 'sad', 'Missing someone you lost and wishing you could go back to the beginning.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Breathin', 'Ariana Grande', 'anxious', 'For anxiety that makes it hard to breathe. A reminder to just keep breathing.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Stressed Out', 'twenty one pilots', 'anxious', 'Pressure about the future, deadlines and growing up, said out loud.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Unwell', 'Matchbox Twenty', 'anxious', 'When overthinking makes you feel strange in your own head. You''re not the only one.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Shake It Out', 'Florence + the Machine', 'anxious', 'Before an exam or interview, when the worry is loud and you need to shake it off.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Breathe (2 AM)', 'Anna Nalick', 'anxious', 'Can''t sleep, mind racing at 2am. Slow down and breathe.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Killing in the Name', 'Rage Against the Machine', 'angry', 'Furious at something unfair. Let the anger out loud instead of holding it in.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Numb', 'Linkin Park', 'angry', 'Frustrated and fed up with being pushed to be someone you''re not.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Before He Cheats', 'Carrie Underwood', 'angry', 'Betrayed and mad at someone who lied to you. Sing it, don''t do it.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Zinda', 'Siddharth Mahadevan', 'angry', 'Turn the rage into fuel. Angry energy for a hard workout or a run.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Seven Nation Army', 'The White Stripes', 'angry', 'Irritated and ready to push back. A steady stomp for walking it off.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Eleanor Rigby', 'The Beatles', 'lonely', 'For feeling invisible, like nobody notices you. All the lonely people.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Dancing On My Own', 'Robyn', 'lonely', 'Left out and alone in a crowded room. Dance anyway.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Boulevard of Broken Dreams', 'Green Day', 'lonely', 'Walking alone at night, far from everyone, with only your own company.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Space Song', 'Beach House', 'lonely', 'Isolated and drifting, missing someone who feels very far away.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Phir Le Aya Dil', 'Arijit Singh', 'lonely', 'Living away from home and missing everyone. The heart keeps wandering back.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Let It Be', 'The Beatles', 'drained', 'Exhausted after a long day and too tired to fix anything. Let it be for tonight.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Holocene', 'Bon Iver', 'drained', 'Burnt out and small. A slow, quiet song for resting your head.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Iktara', 'Kavita Seth', 'drained', 'Worn out and searching for yourself again. Gentle, like a deep breath.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Easy On Me', 'Adele', 'drained', 'When you have no energy left and need people, including you, to go easy on you.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Banana Pancakes', 'Jack Johnson', 'drained', 'Overworked and sleepy. Permission for a slow morning and staying in.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Summer of ''69', 'Bryan Adams', 'nostalgic', 'Remembering the best days of your life, back when everything felt possible.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Yaaron', 'KK', 'nostalgic', 'School days and college friends. For a reunion or old photos with your people.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Pal', 'KK', 'nostalgic', 'Farewell-day memories. The moments you used to think would last forever.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('1985', 'Bowling for Soup', 'nostalgic', 'Funny nostalgia for growing up and realising the old days are years ago.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Photograph', 'Ed Sheeran', 'nostalgic', 'Memories kept in old photos, for missing people you love from back then.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Kal Ho Naa Ho', 'Sonu Nigam', 'nostalgic', 'Childhood throwback that also reminds you to love today while it''s here.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Clair de Lune', 'Claude Debussy', 'calm', 'Quiet and peaceful. For a slow evening, rain outside and nothing to rush.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Weightless', 'Marconi Union', 'calm', 'Made to slow your breathing down. For settling a busy mind into calm.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Kun Faya Kun', 'A.R. Rahman, Javed Ali, Mohit Chauhan', 'calm', 'Peace and stillness, the kind that feels like being held.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Bloom', 'The Paper Kites', 'calm', 'Soft and content. A cozy song for a quiet morning with tea.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Sunset Lover', 'Petit Biscuit', 'calm', 'Relaxed and chill, like watching the sky go orange at the end of the day.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Here Comes the Sun', 'The Beatles', 'hopeful', 'After a long hard winter, things are finally getting better.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Rise Up', 'Andra Day', 'hopeful', 'Down but not done. For trying again and believing you''ll get back up.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Aashayein', 'KK, Salim-Sulaiman', 'hopeful', 'New hopes and a fresh start. For when you''re ready to begin again.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Unstoppable', 'Sia', 'hopeful', 'Looking forward with strength. Tomorrow feels like something you can face.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Kabhi Kabhi Aditi', 'Rashid Ali', 'hopeful', 'Sad today, but it will pass. A gentle promise that things will be okay.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Lean on Me', 'Bill Withers', 'hopeful', 'For lonely days: you''re not alone, and someone will help you carry it.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');
insert into capsules (song, artist, mood, note, author, source, created_at) values ('Fight Song', 'Rachel Platten', 'hopeful', 'Healing and finding your voice again after a hard stretch.', 'MoodIfy starter set', 'starter', '2026-10-30T17:32:47+00:00');

create index if not exists capsules_wall on capsules (status, source, id);
create index if not exists capsules_submitter on capsules (submitter, created_at);
